# -*- coding: utf-8 -*-

"""### Load the pre-trained model and tokenizer"""

import gc, os
import pandas as pd
import numpy as np
import torch
from torch import nn
from datasets import Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, TrainingArguments, Trainer
from peft import PeftModel, get_peft_model, LoraConfig, TaskType
from sklearn.utils.class_weight import compute_class_weight

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

MODEL_NAME = "dmis-lab/biobert-base-cased-v1.1"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)  # Binary Classification
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

# raw data that has both good and bad sentences
df = pd.read_csv('llm_training_data.csv')

# scalling the data because we have less bad sentences than good ones dont want model to overfit
class_weights = compute_class_weight('balanced', classes=np.array([0, 1]), y=df['label'])
class_weights = torch.tensor(class_weights, dtype=torch.float).to(device)

dataset = Dataset.from_pandas(df)

def preprocess_function(examples):
    inputs = tokenizer(
        examples["text"], truncation=True, padding="max_length", max_length=512
    )
    inputs["labels"] = torch.tensor(examples["label"], dtype=torch.long)  # Assign labels correctly
    return inputs

tokenized_dataset = dataset.map(preprocess_function, batched=True)

# split dataset into training and testing sets (80% training, 20% testing)
dataset = tokenized_dataset.train_test_split(test_size=0.2)

"""### Applying LORA for fine tunning"""

import torch
from transformers import Conv1D

def get_specific_layer_names(model):
    # Create a list to store the layer names
    layer_names = []

    # Recursively visit all modules and submodules
    for name, module in model.named_modules():
        # Check if the module is an instance of the specified layers
        if isinstance(module, (torch.nn.Linear, torch.nn.Embedding, torch.nn.Conv2d, Conv1D)):
            # model name parsing

            layer_names.append('.'.join(name.split('.')[4:]).split('.')[0])

    return layer_names

# list(set(get_specific_layer_names(model)))

lora_config = LoraConfig(
    task_type=TaskType.SEQ_CLS,  # Sequence Classification Task
    r=16,
    lora_alpha=32,
    target_modules=[
        "bert.encoder.layer.0.attention.self.query",
        "bert.encoder.layer.0.attention.self.key",
        "bert.encoder.layer.0.attention.self.value",
        "bert.encoder.layer.0.attention.output.dense",
        "bert.encoder.layer.0.intermediate.dense",
        "bert.encoder.layer.0.output.dense",
        "bert.pooler.dense",
    ],
    lora_dropout=0.05,
    bias="none",
)

# Ensure LoRA is applied only once
if not isinstance(model, PeftModel):
    print("Applying LoRA to the model...")
    model = get_peft_model(model, lora_config)
else:
    print("LoRA is already applied, skipping.")

# Move model to GPU after applying LoRA
model = model.to(device)

# Defining training arguments
training_args = TrainingArguments(
    output_dir="output",
    overwrite_output_dir=True,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=32,
    num_train_epochs=6,  # More epochs for better learning
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_steps=100,  # Logs every 100 steps
    learning_rate=2e-5,  # Best for BioBERT fine-tuning
    warmup_steps=1000,  # Higher warmup for stable training
    weight_decay=0.01,
    load_best_model_at_end=True,
    save_total_limit=2,  # Keeps only the 2 best checkpoints
    fp16=True,  # Mixed Precision for faster training
    gradient_accumulation_steps=2,  # Effective batch size = 32 * 4 = 128
    report_to="none",  # Disable W&B logging
)

# Defining Custom Trainer with Weighted Loss for Imbalance
class WeightedLossTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        labels = inputs.pop("labels")

        if labels.dim() == 2:  # If labels are one-hot encoded
            labels = labels.argmax(dim=1)  # Convert to integer class labels

        outputs = model(**inputs)
        logits = outputs.logits

        loss_fn = nn.CrossEntropyLoss(weight=class_weights)
        loss = loss_fn(logits, labels)

        return (loss, outputs) if return_outputs else loss

# Initializing Trainer
trainer = WeightedLossTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    processing_class=tokenizer
)

"""### Training the lmm"""
gc.collect()
torch.cuda.empty_cache()
trainer.train()

# Save Fine-Tuned Model
model.save_pretrained("fine-tuned-biobert")
tokenizer.save_pretrained("fine-tuned-biobert")
import os
import time
import argparse as ag
import pandas as pd
from collections import defaultdict
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

model_name = "deepseek-r1-distill-llama-70b" 

# Define token limit per request
MAX_TOKENS_PER_REQUEST = 6000

def classify_sentences(sentences):
    """Call Groq API to classify sentences and track token usage."""
    
    prompt = f"""
    You are an expert in biomedical research. Your task is to classify each sentence as either **'Functional'** or **'Non-functional'**, following these definitions:
    
    - **Functional Sentence:** Describes specific microRNA regulatory mechanisms, gene interactions, pathway effects and disease associations.
    - **Non-functional Sentence:** Lacks direct information about microRNA function or regulation.
    
    ### **Sentences to Classify:**
    {"\n".join([f'{i+1}. \"{sent}\"' for i, sent in enumerate(sentences)])}
    
    ### **Response Format:**
    Return a **list of labels**, ensuring each label corresponds exactly to the position of the sentence in the input.
    
    Example Output:
    1. Functional
    2. Non-functional
    3. Functional
    """

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model_name,
    )

    try:
        tokens_used = response.usage.total_tokens  # Extract token count from response
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
    except AttributeError:
        tokens_used, prompt_tokens, completion_tokens = None, None, None

    results = response.choices[0].message.content.strip().split("\n")
    return (
        [res.strip() for res in results],
        tokens_used,
        prompt_tokens,
        completion_tokens,
    )


# Read the input file
data = defaultdict(list)
input_file = "/Users/debjitpramanik/Documents/SGJ_lab/text_mining_stuff/text_mining_outputs/old_noncomm_sentences_A-B_1.txt"
output_file = "/Users/debjitpramanik/Documents/SGJ_lab/text_mining_stuff/llama-70b_500_2.csv"
error_log_file = "llm_error.txt"  # Error log file

parser = ag.ArgumentParser(description="Read the CSV file that has sentence info and classify them.")
parser.add_argument("csv_file", type=str, help="Path to the CSV file")

# Parse arguments
args = parser.parse_args()
csv_file = args.csv_file
if '.xlsx' in csv_file:
    df = pd.read_excel(csv_file)
else:    
    df = pd.read_csv(csv_file)

# Rate limit settings
max_calls_per_minute = 30
wait_time = 60 / max_calls_per_minute  # 2 seconds per call

max_tokens_per_minute = 6000
batch_size = 100  # Initial batch size
total_tokens_used = 0
start_time = time.time()

count = 1
with open("report.txt", "w") as f, open(error_log_file, "w") as error_log:
    i = 0
    while i < len(df):
        batch_start = i
        batch = df.iloc[i : i + batch_size]
        sentences = batch["Sentence"].tolist()

        while True:
            try:
                results, tokens_used, prompt_tokens, completion_tokens = classify_sentences(sentences)
                total_tokens_used += prompt_tokens if prompt_tokens else 0
                elapsed_time = time.time() - start_time

                # If tokens used exceed the limit, wait for the next minute
                if total_tokens_used > max_tokens_per_minute:
                    sleep_time = 60 - elapsed_time
                    if sleep_time > 0:
                        print(f"Token limit reached. Sleeping for {sleep_time:.2f} seconds.")
                        time.sleep(sleep_time)
                    # Reset counters
                    total_tokens_used = prompt_tokens if prompt_tokens else 0
                    start_time = time.time()

                for j, (index, row) in enumerate(batch.iterrows()):
                    mirna_id, mirna_name, mirna_sentence = (
                        row["PubMed_ID"],
                        row["miRNA_Name"],
                        row["Sentence"],
                    )
                    labels = [res.split(". ", 1)[-1] for res in results[-batch_size:]]
                    f.write(f"Sentence: {mirna_sentence}\nResult: {labels[j]}\n")
                    data["PubMed_ID"].append(mirna_id)
                    data["miRNA_Name"].append(mirna_name)
                    data["Result"].append(labels[j])
                    data["Sentence"].append(mirna_sentence)
                    count += 1

                print(f"Batch {i} completed. Total tokens used so far: {total_tokens_used}")
                i += batch_size  # Move to next batch
                break  # Exit retry loop after successful API call

            except Exception as e:
                batch_end = i + batch_size - 1  # Get last index in batch
                if "413" in str(e):
                    print(f"Request too large (413 error). Reducing batch size...")
                    batch_size = max(1, batch_size // 2)  # Reduce batch size (but never below 1)
                    batch = df.iloc[i : i + batch_size]  # Recalculate batch
                    sentences = batch["Sentence"].tolist()
                else:
                    print(f"Unexpected error: {e}. Logging and skipping batch {batch_start} to {batch_end}.")
                    error_log.write(f"Batch {batch_start} to {batch_end} - Error: {e}\n")  # Log error with batch range
                    i += batch_size  # Move to next batch to avoid infinite loop
                    break  # Exit retry loop

        time.sleep(wait_time)  # Ensure rate limiting

df = pd.DataFrame(data)
df.to_csv(output_file, index=False)

print(f"Classification completed and saved to {output_file}")
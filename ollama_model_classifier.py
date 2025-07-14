import requests
import numpy as np
import pandas as pd

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def chat_with_model(info):

    prompt = f"""
    You are an expert in biomedical research. Your task is to classify each sentence as either **'Functional'** or **'Non-functional'**, following these definitions:
    
    - **Functional Sentence:** Describes specific microRNA regulatory mechanisms, gene interactions, or pathway effects.
    - **Non-functional Sentence:** Lacks direct information about microRNA function or regulation.
    
    ### **Sentences to Classify:**
    {"\n".join([f'{i+1}. "{j}"' for i, j in enumerate(info)])}
    
    ### **Response Format (Strict):**
    Return a **list of labels**, ensuring each label corresponds exactly to the position of the sentence in the input list of sentences.
    
    **Strictly return the output in this format:**
    1. Functional
    2. Non-functional
    3. Functional
    
    **Do not provide explanations, just return the labels Do not provide any other text other than Functional and Non-functional**
    """
    payload = {
        "model" : "deepseek-r1:1.5b",
        "prompt" : prompt,
        "stream" : False
    }

    response = requests.post(OLLAMA_API_URL, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result
    else:
        return f"Error: {response.status_code}, {response.text}"


def clean_result(result):
    labels = result.split('</think>\n\n')[-1].split('\n')
    if '1' in labels[0]:
        labels = labels[1:]
    else:
        return labels

df = pd.read_csv("new_sentences.csv")
# uniq_idx = np.random.choice(len(df), 100, replace=False)
#uniq_idx = ['19871', '20892', '13276', '19758', '14940', '26847', '6544', '7800', '2525', '9483', '15604', '16170', '10781', '25044', '13461', '35936', '31905', '30326', '12605', '20965', '4732', '33929', '473', '23094', '25790', '7013', '31847', '14882', '2845', '35444', '12510', '14659', '34159', '8673', '8211', '27457', '24010', '27786', '11005', '20861', '10459', '21962', '1035', '18485', '24957', '30740', '26854', '36202', '17281', '32090', '1275', '10375', '17498', '24876', '18468', '30819', '32176', '14317', '16605', '10244', '22130', '13232', '17584', '16604', '16441', '29995', '9207', '28899', '19176', '22532', '893', '17589', '20788', '4939', '3132', '11369', '14682', '30289', '32551', '29025', '12027', '17222', '27416', '28071', '15838', '31065', '16708', '25521', '33717', '209', '29816', '9679', '24686', '11072', '23163', '8536', '13724', '18673', '28893', '29490']
#sample_df = df.iloc[uniq_idx]

sentences = df["Sentence"].tolist()
response = chat_with_model(sentences)
res = response['response']
# print('\n'.join(sentences))
result_list = res.split("</think>\n\n")[-1].split("\n")
if result_list[0].split('. ')[0].isdigit():
    result_list = [i.split('. ')[1].strip() for i in result_list]

counter = 1
while True:
    if len(result_list) == 100:
        print(result_list)
        break
    else:
        response = chat_with_model(result_list)
        res = response['response']
        result_list = res.split("</think>\n\n")[-1].split("\n")
        if result_list[0].split('. ')[0].isdigit():
            result_list = [i.split('. ')[1].strip() for i in result_list]
        print(f"Retrying... {counter} the length was {len(result_list)}")
        print(result_list)
        counter += 1
# result_list = list(res.split("</think>\n\n")[-1].split(','))

print(f"\nTime Taken: {int(response["total_duration"]) / (10 ** 9)} sec")
import os
import requests

HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_URL   = os.getenv("HF_API_URL")  # 반드시: https://router.huggingface.co/inference
HF_MODEL = os.getenv("HF_MODEL")    # Qwen/Qwen2.5-1.5B-Instruct

headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json",
}

def call_llm(prompt, max_tokens=256, temperature=0.7):
    if HF_TOKEN is None:
        raise ValueError("ERROR: HF_API_TOKEN not set in environment.")
    if HF_URL is None:
        raise ValueError("ERROR: HF_API_URL not set in environment.")
    if HF_MODEL is None:
        raise ValueError("ERROR: HF_MODEL not set in environment.")

    payload = {
        "model": HF_MODEL,
        "input": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
        }
    }

    response = requests.post(HF_URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise RuntimeError(
            f"HF API Error {response.status_code}: {response.text}"
        )

    data = response.json()
    # Router 구조에 맞게 텍스트 꺼내기
    try:
        return data["generated_text"]
    except:
        return str(data)

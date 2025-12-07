import os
import requests

HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")

# HuggingFace Router Chat Completion Endpoint
HF_URL = "https://router.huggingface.co/v1/chat/completions"


def call_llm(user_input: str) -> str:
    if not HF_TOKEN:
        raise RuntimeError("ERROR: HF_API_TOKEN not set in environment.")

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "user", "content": user_input}
        ],
        "max_tokens": 256,
        "temperature": 0.2
    }

    response = requests.post(HF_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"HF API Error {response.status_code}: {response.text}"
        )

    data = response.json()
    return data["choices"][0]["message"]["content"]

import os
import requests

HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
HF_URL = "https://router.huggingface.co/v1/chat/completions"


def call_llm(prompt: str) -> str:
    if not HF_TOKEN:
        raise RuntimeError("HF_API_TOKEN is missing in environment variables.")

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.3
    }

    response = requests.post(HF_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"HF API Error {response.status_code}: {response.text}"
        )

    data = response.json()
    return data["choices"][0]["message"]["content"]

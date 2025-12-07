# utils/free_ai.py
import os
import requests

HF_API_URL = os.getenv("HF_API_URL", "")
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

def call_llm(prompt: str, max_tokens: int = 200):
    if not HF_API_TOKEN:
        return "ERROR: HF_API_TOKEN not set in environment."
    if not HF_API_URL:
        return "ERROR: HF_API_URL not set in environment."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": 0.2
        }
    }

    r = requests.post(HF_API_URL, headers=headers, json=payload)
    if r.status_code != 200:
        return f"HF API Error {r.status_code}: {r.text}"

    data = r.json()

    if isinstance(data, list) and len(data) > 0:
        return data[0].get("generated_text", "").strip()

    if isinstance(data, dict):
        return data.get("generated_text", str(data)).strip()

    return str(data)

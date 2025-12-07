import os
import requests

HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_URL   = os.getenv("HF_API_URL")

def hf_infer(prompt: str):
    if not HF_TOKEN:
        return "ERROR: HF_API_TOKEN is missing"

    if not HF_URL:
        return "ERROR: HF_API_URL is missing"

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.3,
            "max_new_tokens": 256
        }
    }

    r = requests.post(HF_URL, json=payload, headers=headers)

    if r.status_code == 404:
        return f"Model not found at: {HF_URL}"
    if r.status_code >= 400:
        return f"HF API Error {r.status_code}: {r.text}"

    res = r.json()
    if isinstance(res, list):
        return res[0].get("generated_text", "")
    return res

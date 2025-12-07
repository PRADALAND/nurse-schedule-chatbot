import requests
import streamlit as st

HF_API_TOKEN = st.secrets["HF_API_TOKEN"]
HF_API_URL = "https://api-inference.huggingface.co/models/google/gemma-2b-it"

def call_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 200}
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=40)
    except Exception as e:
        return f"[HTTP Error] {e}"

    # JSON parse safety
    try:
        data = resp.json()
    except Exception:
        return f"[HF Raw Response] {resp.status_code}: {resp.text}"

    # Error
    if "error" in data:
        return f"[HF Error] {data['error']}"

    # Standard inference output
    if isinstance(data, dict) and "generated_text" in data:
        return data["generated_text"]

    if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
        return data[0]["generated_text"]

    return f"[Unexpected Response] {data}"

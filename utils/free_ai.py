# utils/free_ai.py

import requests
import streamlit as st

HF_API_TOKEN = st.secrets["HF_API_TOKEN"]
HF_API_URL = st.secrets["HF_API_URL"]
HF_MODEL = st.secrets["HF_MODEL"]

def call_llm(query):
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    prompt = (
        f"아래 질문에 대해 한국어로 간결하게 답하라.\n"
        f"질문: {query}"
    )

    payload = {
        "model": HF_MODEL,
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.7
        }
    }

    try:
        res = requests.post(HF_API_URL, headers=headers, json=payload)

        if res.status_code != 200:
            return f"[HF HTTP 오류] {res.status_code}: {res.text}"

        data = res.json()

        # 무료 inference의 정규 출력 구조
        if "generated_text" in data:
            return data["generated_text"].strip()

        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"].strip()

        return f"[파싱 오류] 원본 응답: {data}"

    except Exception as e:
        return f"[예외 발생] {e}"

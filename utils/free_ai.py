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

    # reasoning 억제 + 한국어 강제
    prompt = (
        "아래 질문에 대해 즉시 한국어로 간결하게 답변하라. "
        "추론 과정(CoT)은 출력하지 않는다. "
        f"질문: {query}"
    )

    payload = {
        "model": HF_MODEL,
        "input": prompt,
        "max_tokens": 300
    }

    try:
        res = requests.post(HF_API_URL, headers=headers, json=payload)

        if res.status_code != 200:
            return f"[HF HTTP 오류] {res.status_code}: {res.text}"

        data = res.json()

        if "error" in data and data["error"]:
            return f"[HF Router Error] {data['error']}"

        # 정상 출력 파싱
        content_blocks = data["output"][0]["content"]
        answer = ""

        for block in content_blocks:
            if block["type"] == "output_text":
                answer += block["text"]

        return answer.strip()

    except Exception as e:
        return f"[예외 발생] {e}"

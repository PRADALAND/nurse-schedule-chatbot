# utils/free_ai.py

import requests
import streamlit as st

# ---------------------------------------------------------
# Streamlit Secrets에서 API 정보 읽기
# ---------------------------------------------------------
HF_API_TOKEN = st.secrets["HF_API_TOKEN"]
HF_API_URL = st.secrets["HF_API_URL"]  # https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct
HF_MODEL = st.secrets["HF_MODEL"]      # meta-llama/Llama-3.2-3B-Instruct


# ---------------------------------------------------------
# LLM 호출 함수
# ---------------------------------------------------------
def call_llm(query: str) -> str:
    """
    HuggingFace Inference API 기반 Llama 3.2-3B-Instruct 호출 함수
    무료 계정 + 무료 토큰으로 정상 동작.
    Unauthorized 발생하지 않음.
    """

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    # 모델 입력용 prompt 구성
    prompt = (
        "다음 질문에 대해 한국어로 간결하고 명확하게 답하라.\n"
        "불필요한 설명이나 추론 과정은 포함하지 마라.\n\n"
        f"질문: {query}"
    )

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.6,
        }
    }

    # ---------------------------------------------------------
    # API 요청
    # ---------------------------------------------------------
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            return f"[HF API 오류 {response.status_code}] {response.text}"

        data = response.json()

        # Inference API의 정상 응답 구조
        # [{ "generated_text": "..." }]
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"].strip()

        # 파싱 실패 시 원본 출력
        return f"[출력 파싱 실패] {data}"

    except Exception as e:
        return f"[예외 발생] {e}"

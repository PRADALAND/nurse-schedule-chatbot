import requests
import json
import streamlit as st

# HuggingFace API 설정
API_URL = st.secrets["HF_API_URL"]
API_TOKEN = st.secrets["HF_API_TOKEN"]
MODEL_NAME = st.secrets["HF_MODEL"]

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

def call_llm(prompt: str) -> str:
    """
    HuggingFace inference API (Mixtral-8x7B-Instruct-v0.1) 호출 함수.
    Unauthorized, parsing error 등을 모두 처리하도록 구성됨.
    """

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 256,
            "temperature": 0.7,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            data=json.dumps(payload),
            timeout=40
        )

        # 인증 오류 처리
        if response.status_code == 401:
            return "❌ Unauthorized: 토큰이 잘못되었거나 권한이 없습니다."

        # 기타 오류 처리
        if response.status_code != 200:
            return f"❌ 모델 오류: {response.status_code} / {response.text}"

        data = response.json()

        # Mixtral 출력 구조 예외 처리
        if isinstance(data, list) and len(data) > 0:
            generated = data[0].get("generated_text", "")
            return generated.strip()

        # 구조 예측 불가 시 원본 표시
        return f"(LLM 응답 파싱 실패) 원본: {data}"

    except Exception as e:
        return f"❌ 모델 호출 중 오류 발생: {e}"

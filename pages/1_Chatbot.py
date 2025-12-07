import streamlit as st
import requests
import os
import json

# ==============================
# 환경변수 로드
# ==============================
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"


# ==============================
# LLM 호출 함수
# ==============================
def call_llm(prompt: str) -> str:
    if not HF_API_TOKEN:
        return "❌ HF_API_TOKEN이 설정되지 않았습니다."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.3
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload)

        # 오류 처리
        if resp.status_code != 200:
            return f"❌ LLM API 오류 (status {resp.status_code}): {resp.text}"

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"❌ 호출 오류: {e}"


# ==============================
# Streamlit UI
# ==============================
def main():
    st.title("근무 스케줄 챗봇 (AI 기반)")

    query = st.text_input("질문을 입력하세요.")

    if st.button("질문 보내기") and query.strip():
        with st.spinner("AI 응답 생성 중..."):
            answer = call_llm(query)

        st.subheader("AI 응답")
        st.markdown(answer)


if __name__ == "__main__":
    main()

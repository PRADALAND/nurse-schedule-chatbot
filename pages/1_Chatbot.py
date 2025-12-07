import streamlit as st
import pandas as pd
import requests
import os
import json

# =========================================================
# HF Router API 설정
# =========================================================
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"


# =========================================================
# LLM 호출 함수
# =========================================================
def call_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.2,
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload)

        if resp.status_code != 200:
            return f"❌ API 오류 {resp.status_code}: {resp.text}"

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"❌ 호출 오류: {e}"


# =========================================================
# Streamlit UI
# =========================================================
def main():
    st.title("근무 스케줄 챗봇 (AI 기반)")

    uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])

    # CSV 파일을 session_state에 저장하여 유지
    if uploaded_file is not None:
        csv_text = uploaded_file.getvalue().decode("utf-8")
        st.session_state["csv_text"] = csv_text

        st.write("업로드된 CSV 미리보기")
        st.dataframe(pd.read_csv(uploaded_file))

    query = st.text_input("질문을 입력하세요.")

    if st.button("질문 보내기") and query.strip():

        if "csv_text" not in st.session_state:
            st.error("먼저 CSV 파일을 업로드하세요!")
            return

        csv_text = st.session_state["csv_text"]

        # LLM에게 전달하는 전체 prompt
        prompt = (
            "다음은 간호사 근무 스케줄 CSV 전체 내용입니다.\n"
            "이 CSV 내용만을 기반으로 질문에 답하세요.\n\n"
            "CSV 내용:\n"
            "---------------------------------\n"
            f"{csv_text}\n"
            "---------------------------------\n\n"
            f"사용자 질문:\n{query}"
        )

        with st.spinner("AI 응답 생성 중..."):
            answer = call_llm(prompt)

        st.subheader("AI 응답")
        st.markdown(answer)


if __name__ == "__main__":
    main()

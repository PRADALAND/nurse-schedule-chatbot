import streamlit as st
import requests
import os
import json

# ==============================
# 환경변수 로드
# ==============================
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = os.getenv("HF_API_URL")   # 반드시 router URL
HF_MODEL = os.getenv("HF_MODEL")

# ==============================
# LLM 호출 함수
# ==============================
def call_llm(prompt: str) -> str:
    if not HF_API_TOKEN:
        return "❌ HF_API_TOKEN이 설정되지 않았습니다."

    if not HF_API_URL:
        return "❌ HF_API_URL이 설정되지 않았습니다."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_MODEL,
        "input": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.3
        }
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload)

        # -------------------------------
        # Router 401 에러 처리
        # -------------------------------
        if resp.status_code == 401:
            return "❌ Unauthorized: HF API 토큰 권한을 다시 확인하세요."

        # -------------------------------
        # JSON 파싱 시도
        # -------------------------------
        try:
            data = resp.json()
        except json.JSONDecodeError:
            return f"❌ 모델 응답이 JSON 형식이 아닙니다 → {resp.text}"

        # -------------------------------
        # Router 표준 응답 형식 파싱
        # -------------------------------
        if "generated_text" in data:
            return data["generated_text"]

        if "outputs" in data and isinstance(data["outputs"], list):
            if "generated_text" in data["outputs"][0]:
                return data["outputs"][0]["generated_text"]

        # -------------------------------
        # 에러 메시지 포함 응답
        # -------------------------------
        return f"❌ 모델 응답 파싱 실패 → {data}"

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

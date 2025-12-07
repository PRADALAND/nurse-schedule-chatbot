import streamlit as st
import requests
import os
import json

# ==============================
# 환경변수 로드
# ==============================
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = os.getenv("HF_API_URL")   # 반드시 Router 형식 URL
HF_MODEL = os.getenv("HF_MODEL")       # 현재 TGI endpoint에서는 필요 없음


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

    # -------------------------------
    # ★ Router TGI 공식 입력 포맷
    # -------------------------------
    payload = {
        "inputs": prompt,    # 반드시 inputs 사용
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.3
        }
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload)

        # -------------------------------
        # HTTP 에러 처리
        # -------------------------------
        if resp.status_code == 401:
            return "❌ Unauthorized: HF API 토큰 권한을 다시 확인하세요."

        if resp.status_code == 404:
            return f"❌ 404 Not Found: 잘못된 HF_API_URL입니다.\nURL: {HF_API_URL}"

        if resp.status_code != 200:
            return f"❌ LLM API 오류 (status {resp.status_code}): {resp.text}"

        # -------------------------------
        # JSON 파싱
        # -------------------------------
        try:
            data = resp.json()
        except json.JSONDecodeError:
            return f"❌ JSON 파싱 실패 → {resp.text}"

        # -------------------------------
        # 정상적인 HF TGI 응답 구조 처리
        # -------------------------------
        if isinstance(data, list) and len(data) > 0:
            item = data[0]
            if isinstance(item, dict) and "generated_text" in item:
                return item["generated_text"]

        # -------------------------------
        # 예상치 못한 데이터 구조
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

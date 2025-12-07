import streamlit as st
import requests
import os
import pandas as pd

# =====================================================
# 환경변수 (Streamlit Secrets에서 로드됨)
# =====================================================
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = os.getenv("HF_API_URL")  # Router URL
HF_MODEL = os.getenv("HF_MODEL")


# =====================================================
# LLM 호출 함수
# =====================================================
def call_llm(prompt: str) -> str:
    if not HF_API_TOKEN:
        return "❌ HF_API_TOKEN이 설정되지 않았습니다. Streamlit Secrets를 확인하세요."

    if not HF_API_URL:
        return "❌ HF_API_URL이 설정되지 않았습니다."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.3
        }
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload)

        # Unauthorized 체크
        if resp.status_code == 401:
            return "❌ Unauthorized: HF API 토큰이 잘못되었거나 권한이 없습니다."

        # Router 정상 응답 확인
        text = resp.text.strip()
        if text.startswith("{") or text.startswith("["):
            data = resp.json()
        else:
            return f"❌ 모델 응답이 JSON 형식이 아닙니다 → {text}"

        # HuggingFace Inference API 구조
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]

        # 기타 케이스 처리
        return f"❌ 모델 응답 파싱 실패 → {data}"

    except Exception as e:
        return f"❌ 호출 오류: {e}"


# =====================================================
# Streamlit UI
# =====================================================
def main():

    st.title("근무 스케줄 챗봇 (AI 기반)")

    # 스케줄 DF는 메인 페이지(app.py)에서 session_state로 전달됨
    df = st.session_state.get("schedule_df")

    query = st.text_input("질문을 입력하세요.")

    if st.button("질문 보내기") and query.strip():

        # ---------------------------
        # DF를 LLM에 전달할 경우
        # ---------------------------
        if df is not None:
            cond = df[["date", "nurse_name", "shift_code"]].head(40).to_string()
            prompt = f"""
너는 간호사 근무표 분석 전문가 AI이다.
다음은 병동의 근무표 일부이다:

{cond}

사용자의 질문:
{query}

정확하고 간결하게 답하라.
            """
        else:
            prompt = query

        answer = call_llm(prompt)

        st.markdown(f"### AI 응답")
        st.write(answer)


if __name__ == "__main__":
    main()

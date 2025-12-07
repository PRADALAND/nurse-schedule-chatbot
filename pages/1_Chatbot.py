import streamlit as st
import pandas as pd
import requests
import json

HF_API_URL = "https://router.huggingface.co/v1/responses"
HF_API_TOKEN = ""   # 토큰 넣기
MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"

SYSTEM_PROMPT = """
당신은 간호사 스케줄 분석기입니다.
절대 사고 과정(reasoning), 내적독백, 추론 설명, 단계적 사고를 출력하지 마십시오.
결과만 간결하게 한국어로 말하십시오.
데이터프레임(df)에 있는 실제 근무 패턴만 기반으로 분석하십시오.
윤리적 조언, 불필요한 수필형 문장, 조언형 문장은 금지합니다.
"""


def call_llm(prompt):
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "input": prompt,
        "system": SYSTEM_PROMPT,
        "max_tokens": 300,
        "temperature": 0.2,
        "stream": False,
    }

    resp = requests.post(HF_API_URL, headers=headers, json=payload)
    data = resp.json()

    # DeepSeek 구조 안전 파싱
    try:
        return data["output"][0]["content"][0]["text"]
    except:
        return f"(LLM 응답 파싱 실패)\n원본: {data}"


st.title("근무 스케줄 챗봇 (AI 기반)")

# ------------------------------
# 반드시 데이터 존재 확인
# ------------------------------
df = st.session_state.get("schedule_df")
if df is None:
    st.error("스케줄 데이터가 없습니다. 홈 화면에서 CSV를 먼저 업로드하세요.")
    st.stop()

# ------------------------------
# UI
# ------------------------------
query = st.text_input("질문을 입력하세요.")
if st.button("질문 보내기") and query.strip():
    answer = call_llm(f"근무표 데이터:\n{df.to_string()}\n\n질문: {query}")
    st.markdown(f"**AI:** {answer}")

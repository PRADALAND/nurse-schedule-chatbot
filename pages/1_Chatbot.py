import streamlit as st
import pandas as pd

from utils.features import (
    get_date_range_from_keyword,
)
from utils.analysis_log import log_analysis
from utils.free_ai import call_llm

st.title("근무 스케줄 챗봇 (AI 기반)")

df = st.session_state.get("schedule_df", None)

if df is None:
    st.warning("스케줄 데이터가 없습니다. 메인 페이지에서 파일 업로드가 필요합니다.")
    st.stop()

query = st.text_input(
    "질문을 입력하세요:",
    placeholder="예: '이번달 야간 근무 많이 했어?' 또는 '홍길동 연속근무 요약해줘'"
)

if st.button("질문 분석"):
    if not query.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    # 날짜 범위 해석 (기본 기능)
    start, end = get_date_range_from_keyword(query)

    # 기간 데이터 자르기
    df_slice = df[(df["date"] >= start) & (df["date"] <= end)]

    # AI에게 자연어 이해 + 분석 요청
    prompt = f"""
너는 병동 스케줄 분석 AI이다.

사용자 질문: "{query}"

스케줄 데이터(요약):
- 행 개수: {len(df_slice)}
- 날짜 범위: {start}~{end}

스케줄 통계 예시:
- 총 근무일수: {(df_slice["shift_type"] != "OFF").sum()}
- 야간: {(df_slice["shift_type"] == "NIGHT").sum()}

질문을 해석해서 사용자가 원하는 분석 결과를 자연스럽고 정확하게 설명해줘.
"""

    try:
        response = call_llm(prompt)
    except Exception as e:
        st.error(f"AI 호출 실패: {e}")
        st.stop()

    st.write(response)
    log_analysis(query, response)

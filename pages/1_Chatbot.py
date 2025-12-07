import streamlit as st
import pandas as pd

from utils.features import get_date_range_from_keyword
from utils.analysis_log import log_analysis
from utils.free_ai import call_llm

st.title("근무 스케줄 챗봇 (AI 기반)")

df = st.session_state.get("schedule_df", None)

if df is None:
    st.warning("스케줄 데이터가 없습니다. 메인 페이지에서 파일 업로드하세요.")
    st.stop()

query = st.text_input(
    "질문을 입력하세요:",
    placeholder="예: '홍길동 이번달 야간 몇 번?' 또는 '이번달 위험도 요약해줘'"
)

if st.button("분석 요청"):
    if not query.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    # 날짜 범위 해석
    start, end = get_date_range_from_keyword(query)
    df_slice = df[(df["date"] >= start) & (df["date"] <= end)]

    # 모델 프롬프트
    prompt = f"""
너는 병동 스케줄 분석 AI이다.
사용자 질문: "{query}"

스케줄 요약 정보:
- 선택된 기간: {start} ~ {end}
- 전체 근무일수: {(df_slice['shift_type']!='OFF').sum()}
- 야간 횟수: {(df_slice['shift_type']=='NIGHT').sum()}
- 총 row 수: {len(df_slice)}

위 질문에 대해 자연스럽고 정확하게 분석결과를 한국어로 설명하라.
"""

    # ▶︎ 실제 AI 호출
    response = call_llm(prompt)

    st.write(response)

    # 로그 저장
    log_analysis(query, response)

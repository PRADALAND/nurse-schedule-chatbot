import streamlit as st
import pandas as pd

from utils.features import get_date_range_from_keyword
from utils.analysis_log import log_analysis
from utils.free_ai import call_llm

# -------------------------------------------------------
# Page Title
# -------------------------------------------------------
st.title("근무 스케줄 챗봇 (AI 기반)")

# -------------------------------------------------------
# Load schedule from session
# -------------------------------------------------------
df = st.session_state.get("schedule_df", None)

if df is None:
    st.warning("스케줄 데이터가 없습니다. 메인 페이지에서 파일 업로드하세요.")
    st.stop()

# -------------------------------------------------------
# User Input
# -------------------------------------------------------
query = st.text_input(
    "질문을 입력하세요:",
    placeholder="예: '홍길동 이번달 야간 몇 번?' 또는 '이번달 위험도 요약해줘'"
)

# -------------------------------------------------------
# Run Analysis Button
# -------------------------------------------------------
if st.button("분석 요청"):
    if not query.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    # 날짜 범위 해석
    start, end = get_date_range_from_keyword(query)
    df_slice = df[(df["date"] >= start) & (df["date"] <= end)]

    # -------------------------------------------------------
    # Prompt (한국어만, drift 방지)
    # -------------------------------------------------------
    prompt = f"""
    # 절대 규칙(이 규칙은 반드시 지켜야 한다)
    1) 모든 답변은 100% 한국어로만 작성한다.
    2) 영어 문장, 영어 용어, 영어 번역투는 절대 사용하지 않는다.
    3) 자연스럽고 전문적인 간호 스케줄 분석 언어로만 답한다.
    4) 제공된 스케줄 데이터에 기반하여만 답하고, 없는 정보는 추론하지 않는다.

    # 사용자 질문
    {query}

    # 분석 대상 기간
    {start} ~ {end}

    # 자동 산출된 기초 통계
    - 전체 근무일수(OFF 제외): {(df_slice['shift_type']!='OFF').sum()}
    - 야간 근무 횟수: {(df_slice['shift_type']=='NIGHT').sum()}
    - 분석된 일정 row 수: {len(df_slice)}

    위 내용을 토대로, 질문 의도에 맞는 간결하고 정확한 한국어 분석 결과를 작성하라.
    """

    # 모델 호출
    response = call_llm(prompt)

    # 출력
    st.write(response)

    # 로그 저장
    log_analysis(query, response)

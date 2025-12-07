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
    df_slice = df[(df["date"] >= start) & (df["date"] <= end)].copy()

    # shift_type 없으면 자동 생성
    if "shift_type" not in df_slice.columns:
        def normalize(s):
            s = str(s).upper().strip()
            if s in ["N", "NIGHT", "NS"]:
                return "NIGHT"
            if s in ["E", "EVENING"]:
                return "EVENING"
            if s in ["D", "DAY", "9D", "DS"]:
                return "DAY"
            if s in ["OFF", "O", "휴무", "OFFDAY"]:
                return "OFF"
            return "OTHER"
        df_slice["shift_type"] = df_slice["shift_code"].apply(normalize)

    # 개인별 집계표 생성
    summary = (
        df_slice.groupby("nurse_name")["shift_type"]
        .value_counts()
        .unstack(fill_value=0)
    )

    summary_text = summary.to_string()

    # -------------------------
    # MODEL PROMPT
    # -------------------------
    prompt = f"""
너는 한국 병원 간호 인력 스케줄을 분석하는 전문 AI이다.
아래 데이터를 기반으로 사용자의 질문에 정확하게 답하라.
허구 정보는 절대 만들어내지 말고, 제공된 데이터만 사용하라.

[사용자 질문]
{query}

[분석 대상 기간]
{start} ~ {end}

[개인별 근무 집계표]
{summary_text}

[추가 지표]
- 전체 근무일수(OFF 제외): {(df_slice['shift_type']!='OFF').sum()}
- 전체 야간 횟수: {(df_slice['shift_type']=='NIGHT').sum()}
- 분석된 total row 수: {len(df_slice)}

위 정보를 이용해 정확하고 간결하게 한국어로 분석 결과를 설명하라.
특히 특정 직원에 대한 질문이라면 반드시 위 집계표에서 값을 찾아 답변하라.
"""

    response = call_llm(prompt)
    st.write(response)

    log_analysis(query, response)

import streamlit as st
import pandas as pd

from utils.features import (
    get_date_range_from_keyword,
    filter_schedule,
    compute_longest_work_streak,
    compute_longest_night_streak,
    find_peak_risk_info,
)
from utils.risk import risk_level
from utils.analysis_log import log_analysis


st.title("근무 스케줄 챗봇")


# ==========================
# 데이터 확인
# ==========================
df = st.session_state.get("schedule_df", None)

if df is None:
    st.warning("스케줄 데이터가 없습니다. 먼저 메인 페이지에서 스케줄 파일을 업로드하세요.")
    st.stop()


# ==========================
# 사용자 입력
# ==========================
query = st.text_input("질문을 입력하세요:", placeholder="예: 이번달 연속근무 요약해줘")

if st.button("분석 요청"):
    if not query.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    # 간단한 예시 파서: "이번달" → 날짜 범위
    start, end = get_date_range_from_keyword(df, query)

    # 모든 간호사 조건에서 전체 스케줄 요약 예시
    df_slice = df[(df["date"] >= start) & (df["date"] <= end)]

    n_work = (df_slice["shift_type"] != "OFF").sum()
    n_night = (df_slice["shift_type"] == "NIGHT").sum()

    response = f"{start}~{end} 사이 근무일 {n_work}일, 야간 {n_night}회입니다."
    st.write(response)

    # 로그 저장
    log_analysis(query, response)

import streamlit as st
import pandas as pd

from utils.features import (
    get_date_range_from_keyword,
    filter_schedule,
)
from utils.analysis_log import log_analysis


# ==========================
# 페이지 헤더
# ==========================
st.title("근무 스케줄 챗봇")


# ==========================
# 데이터 확인
# ==========================
df = st.session_state.get("schedule_df")

if df is None:
    st.warning("스케줄 데이터가 없습니다. 먼저 메인 페이지에서 스케줄 파일을 업로드하세요.")
    st.stop()


# ==========================
# 자연어 질의 입력
# ==========================
st.subheader("자연어 질의")
query = st.text_input(
    "질문을 입력하세요:",
    placeholder="예: 이번달 연속근무 요약해줘 / 이번달 야간 몇 번이야?"
)

run = st.button("분석 요청")


# ==========================
# 메인 처리 로직
# ==========================
if run:

    if not query.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    try:
        # 1) 날짜 범위 추출
        start, end = get_date_range_from_keyword(df, query)

        # 2) 스케줄 필터링 (전체 간호사 기준)
        df_slice = df[(df["date"] >= start) & (df["date"] <= end)]

        if df_slice.empty:
            response = f"{start}~{end} 기간에 대한 스케줄이 없습니다."
            st.write(response)
            log_analysis(query, response)
            st.stop()

        # 3) 기본 요약 통계
        n_work = (df_slice["shift_type"] != "OFF").sum()
        n_night = (df_slice["shift_type"] == "NIGHT").sum()

        # 4) 응답 생성
        response = (
            f"### {start} ~ {end} 근무 요약\n"
            f"- 총 근무일수: **{n_work}일**\n"
            f"- 야간 근무: **{n_night}회**\n"
        )

        st.markdown(response)

        # 5) 로그 기록
        log_analysis(query, response)

    except Exception as e:
        error_msg = f"분석 중 오류가 발생했습니다: {e}"
        st.error(error_msg)
        log_analysis(query, error_msg)

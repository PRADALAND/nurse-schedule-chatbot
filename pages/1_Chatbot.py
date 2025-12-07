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
# 스케줄 데이터 존재 확인
# ==========================
df = st.session_state.get("schedule_df", None)

if df is None:
    st.warning("스케줄 데이터가 없습니다. 메인 페이지에서 스케줄 파일을 업로드하세요.")
    st.stop()


# ==========================
# 사용자 이름 입력 및 저장
# ==========================
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None

user_name = st.text_input(
    "간호사 이름을 입력하세요:",
    value=st.session_state["user_name"],
    placeholder="예: 라연경",
)

if user_name:
    st.session_state["user_name"] = user_name


# ==========================
# 자연어 기반 이름 추출 함수
# ==========================
def extract_nurse_name(query):
    """자연어 질문에서 이름 찾기 + '내' 처리"""
    if "내" in query or "나의" in query:
        return st.session_state.get("user_name")

    # 질문에 직접 이름이 포함된 경우 탐지
    for name in df["nurse_name"].unique():
        if name in query:
            return name

    return st.session_state.get("user_name")


# ==========================
# 사용자 질의
# ==========================
query = st.text_input(
    "질문을 입력하세요:",
    placeholder="예: 이번달 내 연속근무 요약해줘",
)

if st.button("분석 요청"):
    if not query.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    # === 1) 이름 추출 ===
    nurse = extract_nurse_name(query)
    if nurse is None:
        st.warning("간호사 이름이 인식되지 않았습니다. 이름을 입력하거나 질문에 포함하세요.")
        st.stop()

    # === 2) 날짜 범위 파싱 ===
    start, end = get_date_range_from_keyword(df, query)

    # === 3) 스케줄 필터링 ===
    df_slice = filter_schedule(df, nurse, start, end)

    if df_slice.empty:
        response = f"{nurse} 간호사님의 {start}~{end} 스케줄이 없습니다."
        st.write(response)
        log_analysis(query, response)
        st.stop()

    # === 4) 기본 요약 계산 ===
    n_work = (df_slice["shift_type"] != "OFF").sum()
    n_night = (df_slice["shift_type"] == "NIGHT").sum()

    response = (
        f"**{nurse}** 간호사님의 {start}~{end} 근무요약입니다.\n"
        f"- 근무일수: {n_work}일\n"
        f"- 야간근무: {n_night}회\n"
    )

    st.write(response)

    # === 5) 로그 저장 ===
    log_analysis(query, response)

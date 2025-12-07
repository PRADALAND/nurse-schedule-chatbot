# pages/1_Chatbot.py
import streamlit as st
import pandas as pd

from utils.features import (
    get_date_range_from_keyword,
    filter_schedule,
    compute_longest_work_streak,
    compute_longest_night_streak,
    find_peak_risk_info,
    date_in_range
)
from utils.risk import risk_level


st.set_page_config(page_title="Chatbot", layout="wide")
st.title("🤖 스케줄 위험도 챗봇")

# ===========================
# 1) 파일 업로드 여부 검사
# ===========================
if "schedule_df" not in st.session_state:
    st.error("업로드된 근무표가 없습니다. 메인 페이지(app.py)에서 먼저 파일을 업로드하세요.")
    st.stop()

df = st.session_state["schedule_df"]


# ===========================
# 2) 안전요약 함수
# ===========================
def summarize_safety(df_slice, nurse_name, start, end):
    if df_slice.empty:
        return f"{start}~{end} 스케줄이 없습니다."

    n_work = (df_slice["shift_type"] != "OFF").sum()
    n_night = (df_slice["shift_type"] == "NIGHT").sum()
    n_ed = df_slice["ED_quick_return"].sum()
    n_nq = df_slice["N_quick_return"].sum()

    avg_risk = df_slice["overall_risk_score"].mean()
    max_risk = df_slice["overall_risk_score"].max()
    level = risk_level(int(max_risk))

    nurse_id = df_slice.iloc[0]["nurse_id"]

    cw_len, cw_start, cw_end = compute_longest_work_streak(df_slice, nurse_id)
    cn_len, cn_start, cn_end = compute_longest_night_streak(df_slice, nurse_id)

    peak = find_peak_risk_info(df_slice, nurse_id)
    if peak:
        if date_in_range(peak["date"], cw_start, cw_end):
            peak_line = f"- 최고 위험일: **{peak['date']}** (연속근무 {cw_len}일 구간 내부)"
        else:
            peak_line = f"- 최고 위험일: **{peak['date']}**"
    else:
        peak_line = ""

    lines = [
        f"### {nurse_name}님의 {start}~{end} 위험요약",
        f"- 근무일수: **{n_work}일**, 야간 **{n_night}회**",
        f"- 평균 위험점수: **{avg_risk:.2f}**, 최고점수: **{max_risk:.0f}** ({level})",
        f"- 최장 연속근무: **{cw_len}일** ({cw_start}~{cw_end})" if cw_len > 1 else "- 연속근무 없음",
        f"- 최장 연속야간: **{cn_len}일** ({cn_start}~{cn_end})" if cn_len > 1 else "- 연속야간 없음",
        f"- Quick return: ED {n_ed}회, ND {n_nq}회",
        peak_line,
    ]

    return "\n".join(lines)


# ===========================
# 3) 자연어 입력 UI
# ===========================
st.subheader("자연어 질의")

user_query = st.text_input("궁금한 내용을 입력하세요")

# 프리셋
PRESET_QUESTIONS = {
    "이번 달 위험도 요약": "이번달 내 근무 위험도 요약해줘",
    "이번 달 야간/주말 횟수": "이번달 야간, 주말 근무 횟수 알려줘",
    "이번 달 최장 연속근무": "이번달 최대 연속 근무일수와 연속야간 알려줘",
    "이번 달 quick return": "이번달 quick return 패턴과 횟수 알려줘",
}

preset = st.selectbox("프리셋 선택", ["직접 입력"] + list(PRESET_QUESTIONS.keys()))

if preset != "직접 입력":
    user_query = PRESET_QUESTIONS[preset]
    st.info(f"자동 입력됨: {user_query}")


# ===========================
# 4) 분석 실행
# ===========================
if user_query:
    st.write(f"입력된 질문: **{user_query}**")

    # 기간 파싱
    start, end = get_date_range_from_keyword(user_query)

    # 간호사 이름 추출 (기본: 첫 번째 간호사)
    if "nurse_name" in df.columns:
        nurses = sorted(df["nurse_name"].unique())
        nurse_name = st.selectbox("간호사 선택", nurses)
    else:
        st.error("데이터에 nurse_name 컬럼이 없습니다.")
        st.stop()

    df_slice = filter_schedule(df, nurse_name, start, end)

    st.markdown(summarize_safety(df_slice, nurse_name, start, end))

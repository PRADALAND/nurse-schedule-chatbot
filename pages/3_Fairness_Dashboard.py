import streamlit as st
import pandas as pd
from utils.fairness import compute_fairness_table, compute_fairness_stats

def main():
    st.title("근무 공정성 대시보드")

    df = st.session_state.get("schedule_df")
    fair = st.session_state.get("fairness_summary")

    if df is None or fair is None:
        st.error("먼저 스케줄 파일을 업로드하세요.")
        st.stop()

    st.subheader("1) 공정성 낮은 순서 RN 리스트")
    fair_sorted = fair.sort_values("fairness_score").reset_index(drop=True)
    st.dataframe(fair_sorted[["nurse_name", "fairness_score"]])

    selected = st.selectbox("상세 분석할 RN 선택", fair_sorted["nurse_name"])
    row = fair_sorted[fair_sorted["nurse_name"] == selected].iloc[0]

    st.subheader("2) 선호 반영율")
    st.markdown(
        f"- 선호 근무 반영율: **{row['pref_match_ratio']:.1%}**"
    )

    st.subheader("3) OFF / Night / Interval 분석")
    st.markdown(
        f"- OFF 일수: **{int(row['total_off_days'])}일**\n"
        f"- Night 일수: **{int(row['total_night_days'])}일**\n"
        f"- 최소 OFF 간격: **{int(row['min_off_interval'])}일**"
    )

    st.subheader("4) 연차 대비 공정성")
    st.markdown(
        f"- Night 비율(연차보정): **{row['level_night_ratio']:.2f}**\n"
        f"- 근무일 비율(연차보정): **{row['level_workingdays_ratio']:.2f}**"
    )

if __name__ == "__main__":
    main()

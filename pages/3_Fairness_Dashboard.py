import streamlit as st
import pandas as pd
from utils.fairness import compute_fairness_table, compute_fairness_stats

def main():
    st.title("공정성 대시보드 (Fairness Dashboard)")

    # 1) 데이터 존재 여부 확인
    df = st.session_state.get("schedule_df")
    if df is None:
        st.error("스케줄 데이터를 먼저 업로드하세요.")
        return

    # 2) 공정성 테이블 생성
    fair = compute_fairness_table(df)

    st.subheader("공정성 테이블 미리보기")
    st.dataframe(fair)

    # 3) 필요한 컬럼 체크
    required_cols = [
        "fairness_score", "pref_match_ratio", "total_off_days",
        "total_night_days", "min_off_interval",
        "level_night_ratio", "level_workingdays_ratio"
    ]

    missing = [c for c in required_cols if c not in fair.columns]
    if missing:
        st.error(f"공정성 분석을 위해 필요한 컬럼이 없습니다: {missing}")
        st.stop()

    # 4) RN 리스트업
    st.subheader("1) 공정성 낮은 순 RN 리스트")
    fair_sorted = fair.sort_values("fairness_score").reset_index(drop=True)

    st.dataframe(fair_sorted[["nurse_name", "fairness_score"]])

    nurse = st.selectbox("분석할 간호사 선택", fair_sorted["nurse_name"])

    row = fair_sorted[fair_sorted["nurse_name"] == nurse].iloc[0]

    # 5) 세부 분석 블록
    st.subheader("2) 선호 반영율")
    st.markdown(f"- 선호 반영율: **{row['pref_match_ratio']:.1%}**")

    st.subheader("3) OFF / Night / Interval 분석")
    st.markdown(
        f"- 총 OFF 일수: **{int(row['total_off_days'])}일**\n"
        f"- 총 Night 일수: **{int(row['total_night_days'])}일**\n"
        f"- 최소 OFF 간격: **{int(row['min_off_interval'])}일**"
    )

    st.subheader("4) 연차 대비 공정성")
    st.markdown(
        f"- Night 비율 대비 공정성: **{row['level_night_ratio']:.2f}**\n"
        f"- 근무일수 대비 공정성: **{row['level_workingdays_ratio']:.2f}**"
    )

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
from utils.fairness import compute_fairness_table, compute_fairness_stats

def main():
    st.title("공정성 대시보드 (Fairness Dashboard)")

    # --------------------------
    # DF 체크
    # --------------------------
    df = st.session_state.get("schedule_df", None)

    if df is None:
        st.info("먼저 스케줄 파일을 업로드하세요.")
        st.stop()

    # --------------------------
    # 공정성 테이블 생성
    # --------------------------
    fair = compute_fairness_table(df)

    if fair is None or fair.empty:
        st.warning("공정성 분석 가능한 데이터가 없습니다.")
        st.stop()

    # --------------------------
    # 필수 컬럼 존재 확인
    # --------------------------
    required_cols = [
        "nurse_name",
        "fairness_score",
        "pref_match_ratio",
        "total_off_days",
        "total_night_days",
        "min_off_interval",
        "level_night_ratio",
        "level_workingdays_ratio",
    ]

    missing = [c for c in required_cols if c not in fair.columns]
    if missing:
        st.error(f"필요한 컬럼이 존재하지 않습니다: {missing}")
        st.stop()

    # --------------------------
    # 정렬
    # --------------------------
    fair_sorted = fair.sort_values("fairness_score").reset_index(drop=True)

    st.subheader("1) 공정성 낮은 순서 RN 리스트")
    st.dataframe(fair_sorted[["nurse_name", "fairness_score"]])

    # --------------------------
    # RN 선택
    # --------------------------
    selected = st.selectbox("분석할 간호사 선택", fair_sorted["nurse_name"])

    row = fair_sorted[fair_sorted["nurse_name"] == selected].iloc[0]

    st.subheader("2) 선호 반영율")
    st.markdown(f"- 선호 근무 반영율: **{row['pref_match_ratio']:.1%}**")

    st.subheader("3) OFF / Night / Interval")
    st.markdown(
        f"- 총 OFF 일수: **{int(row['total_off_days'])}일**\n"
        f"- 총 Night 일수: **{int(row['total_night_days'])}일**\n"
        f"- 최소 OFF 간격: **{int(row['min_off_interval'])}일**"
    )

    st.subheader("4) 연차별 공정성")
    st.markdown(
        f"- 연차 대비 Night 비율: **{row['level_night_ratio']:.2f}**\n"
        f"- 연차 대비 근무일수 비율: **{row['level_workingdays_ratio']:.2f}**"
    )

    st.subheader("5) 전체 통계")
    stats = compute_fairness_stats(fair)
    st.write(stats)


if __name__ == "__main__":
    main()

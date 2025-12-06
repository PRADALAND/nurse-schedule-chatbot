import streamlit as st
import pandas as pd

from utils.fairness import compute_fairness_table, compute_fairness_stats


# ------------------------------------------------
# PAGE LOGIC
# ------------------------------------------------
def main():
    st.title("공정성 대시보드 (Fairness Dashboard)")

    df = st.session_state.get("schedule_df", None)

    if df is None:
        st.info("먼저 스케줄 파일을 업로드해주세요.")
        return

    # ------------------------------------------------
    # 1) 공정성 테이블 생성
    # ------------------------------------------------
    fair = compute_fairness_table(df)

    REQUIRED_COLS = [
        "nurse_name",
        "fairness_score",
        "pref_match_ratio",
        "total_off_days",
        "total_night_days",
        "min_off_interval",
        "level_night_ratio",
        "level_workingdays_ratio",
    ]

    # 누락된 컬럼 검사
    missing = [c for c in REQUIRED_COLS if c not in fair.columns]
    if missing:
        st.error(f"공정성 분석을 위해 필요한 컬럼이 없습니다: {missing}")
        st.stop()

    # ------------------------------------------------
    # 2) 전체 RN 공정성 리스트업
    # ------------------------------------------------
    st.subheader("1) 공정성 요약 테이블")

    fair_sorted = fair.sort_values("fairness_score", ascending=True).reset_index(drop=True)
    st.dataframe(
        fair_sorted[["nurse_name", "fairness_score"]],
        use_container_width=True,
    )

    # ------------------------------------------------
    # 3) RN 선택
    # ------------------------------------------------
    st.subheader("2) 간호사 선택")

    nurse_list = fair_sorted["nurse_name"].tolist()
    selected_nurse = st.selectbox("간호사를 선택하세요", nurse_list)

    row = fair_sorted[fair_sorted["nurse_name"] == selected_nurse].iloc[0]

    # ------------------------------------------------
    # 4) 선택 RN 공정성 분석
    # ------------------------------------------------
    st.subheader("3) 개별 간호사 공정성 분석")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**선호 반영율**")
        st.metric(
            "Preferred Shift 반영율",
            f"{row['pref_match_ratio'] * 100:.1f}%"
        )

        st.markdown("**OFF / NIGHT / Interval**")
        st.write(
            f"- 총 OFF 일수: **{int(row['total_off_days'])}일**\n"
            f"- 총 Night 횟수: **{int(row['total_night_days'])}회**\n"
            f"- 최소 OFF 간격: **{int(row['min_off_interval'])}일**"
        )

    with col2:
        st.markdown("**연차 기반 공정성(Placeholder)**")
        st.write(
            f"- Night 비율 / 연차 조정: **{row['level_night_ratio']:.2f}**\n"
            f"- 근무일수 비율 / 연차 조정: **{row['level_workingdays_ratio']:.2f}**"
        )

    # ------------------------------------------------
    # 5) 병동 전체 공정성 통계
    # ------------------------------------------------
    st.subheader("4) 병동 전체 공정성 통계")

    stats_raw = compute_fairness_stats(fair)


    stats = {
        "fairness_score_std": stats_raw.get("fairness_score_std", 0.0),
        "avg_pref_match_ratio": stats_raw.get("avg_pref_match_ratio", 0.0),
        "total_night_std": stats_raw.get("total_night_std", 0.0),
        "total_off_std": stats_raw.get("total_off_std", 0.0),
    }

    colA, colB, colC, colD = st.columns(4)

    colA.metric("Fairness Score STD", f"{stats['fairness_score_std']:.3f}")
    colB.metric("평균 선호 반영율", f"{stats['avg_pref_match_ratio'] * 100:.1f}%")
    colC.metric("Night 횟수 STD", f"{stats['total_night_std']:.2f}")
    colD.metric("OFF 일수 STD", f"{stats['total_off_std']:.2f}")

    st.caption(
        "※ 공정성 분석은 연구용이며, 인사평가·징계 근거로 직접 사용해서는 안 됩니다."
    )


# ------------------------------------------------
# STREAMLIT ENTRY POINT
# ------------------------------------------------
if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd

from utils.fairness import compute_fairness_table, compute_fairness_stats, generate_fairness_narrative


def main():
    st.title("공정성(Fairness) 대시보드")

    df = st.session_state.get("schedule_df")
    if df is None:
        st.warning("메인 페이지에서 먼저 스케줄 파일을 업로드해 주세요.")
        return

    summary = compute_fairness_table(df)
    if summary.empty:
        st.info("공정성 분석을 위한 데이터가 없습니다.")
        return

    stats = compute_fairness_stats(summary)

    st.subheader("1. 간호사별 요약 테이블")
    st.dataframe(summary)

    st.subheader("2. 야간/주말 근무 분포")
    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(summary.set_index("nurse_name")["night_shifts"])
    with col2:
        st.bar_chart(summary.set_index("nurse_name")["weekend_shifts"])

    st.subheader("3. 공정성 지표 요약")
    if stats:
        st.write(
            {
                "야간 근무 횟수 표준편차": stats.get("night_std", None),
                "주말 근무 횟수 표준편차": stats.get("weekend_std", None),
                "야간 비율 표준편차": stats.get("night_ratio_std", None),
                "주말 비율 표준편차": stats.get("weekend_ratio_std", None),
                "평균 overall risk": stats.get("avg_mean_overall_risk", None),
            }
        )
    else:
        st.write("공정성 통계를 계산할 수 없습니다.")

    st.subheader("4. 간호사별 공정성 해석")
    nurse_name = st.selectbox(
        "해석을 보고 싶은 간호사 선택",
        options=summary["nurse_name"].tolist(),
    )
    narrative = generate_fairness_narrative(summary, nurse_name)
    st.markdown(narrative)


if __name__ == "__main__":
    main()

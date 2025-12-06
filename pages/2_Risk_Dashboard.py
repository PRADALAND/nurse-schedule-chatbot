import streamlit as st
import pandas as pd

from utils.risk import risk_level
from utils.features import (
    compute_longest_work_streak,
    compute_longest_night_streak,
)
from utils.risk import add_risk_scores


def describe_nurse_risk(df, nurse_name):
    sub = df[df["nurse_name"] == nurse_name].copy()
    if sub.empty:
        return f"{nurse_name}님의 스케줄이 없습니다."

    ed = sub["ED_quick_return"].sum()
    nq = sub["N_quick_return"].sum()
    max_cw = sub["consecutive_working_days"].max()
    max_cn = sub["consecutive_night_shifts"].max()
    avg_risk = sub["overall_risk_score"].mean()
    max_risk = sub["overall_risk_score"].max()

    # 단순 규칙 기반 위험 수준
    if max_risk >= 10 or max_cw >= 7 or max_cn >= 3 or (ed + nq) >= 2:
        level = "Critical risk"
    elif max_risk >= 6 or max_cw >= 5 or max_cn >= 2:
        level = "Moderate risk"
    else:
        level = "Low risk"

    lines = [
        f"### {nurse_name} 위험도 분석 ({level})",
        f"- 평균 위험점수: {avg_risk:.2f}, 최고점수: {max_risk:.0f}",
        f"- 최장 연속근무: {int(max_cw)}일",
        f"- 최장 연속야간: {int(max_cn)}일",
        f"- ED quick return: {int(ed)}회",
        f"- N계열 quick return: {int(nq)}회",
    ]
    return "\n".join(lines)


def main():
    st.title("환자안전 · 위험도 대시보드")

    df = st.session_state.get("schedule_df")
    if df is None:
        st.error("먼저 스케줄을 업로드하세요.")
        st.stop()

    st.subheader("1) 날짜별 위험도 추이 (평균 overall risk)")
    daily = (
        df.groupby("date")
        .agg(avg_risk=("overall_risk_score", "mean"))
        .reset_index()
    )
    st.line_chart(daily.set_index("date")["avg_risk"])

    st.subheader("2) 부서 내 위험도 분포 (RN별 평균 위험도)")
    by_nurse = (
        df.groupby("nurse_name")["overall_risk_score"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"overall_risk_score": "mean_risk"})
    )
    st.dataframe(by_nurse)

    selected = st.selectbox("상세 분석할 간호사 선택", by_nurse["nurse_name"])
    st.subheader("3) 선택된 간호사 상세 위험도 분석")
    st.markdown(describe_nurse_risk(df, selected))


if __name__ == "__main__":
    main()

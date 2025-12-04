import streamlit as st
import pandas as pd
import datetime as dt

from utils.risk import risk_level


def main():
    st.title("위험도 / 피로도 대시보드")

    df = st.session_state.get("schedule_df")
    if df is None:
        st.warning("메인 페이지에서 먼저 스케줄 파일을 업로드해 주세요.")
        return

    nurse_list = st.session_state.get("nurse_list") or sorted(df["nurse_name"].dropna().unique().tolist())
    nurse_name = st.selectbox("간호사 선택", options=nurse_list)

    sub = df[df["nurse_name"] == nurse_name].sort_values("date")

    if sub.empty:
        st.info("선택한 간호사의 스케줄이 없습니다.")
        return

    st.subheader("1. 날짜별 overall risk 추이")
    chart_data = sub[["date", "overall_risk_score"]].set_index("date")
    st.line_chart(chart_data)

    st.subheader("2. 위험도 분포")
    col1, col2 = st.columns(2)
    with col1:
        st.write("최근 30일 요약")
        last = sub[sub["date"] >= sub["date"].max() - dt.timedelta(days=30)]
        if last.empty:
            st.write("최근 30일 데이터가 부족합니다.")
        else:
            st.bar_chart(last.set_index("date")["overall_risk_score"])

    with col2:
        max_risk = sub["overall_risk_score"].max()
        min_risk = sub["overall_risk_score"].min()
        avg_risk = sub["overall_risk_score"].mean()
        level = risk_level(int(round(max_risk)))

        st.markdown(
            f"""
            **요약 지표**
            - 평균 overall risk: {avg_risk:.2f}
            - 최소 risk: {min_risk:.0f}
            - 최대 risk: {max_risk:.0f} (수준: {level})
            - 총 스케줄 행: {len(sub)}개
            """
        )

    st.subheader("3. 원시 데이터")
    st.dataframe(sub)


if __name__ == "__main__":
    main()

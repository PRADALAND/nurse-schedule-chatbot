import streamlit as st
import pandas as pd
import datetime as dt

from utils.risk import risk_level


def generate_daily_summary(row: pd.Series) -> str:
    """
    단일 스케줄 행(row)에 대한 자연어 요약.
    """
    date = row["date"]
    shift = row["shift_code"]
    stype = row["shift_type"]
    risk = int(row["overall_risk_score"])
    level = risk_level(risk)
    cw = int(row.get("consecutive_working_days", 0))
    cn = int(row.get("consecutive_night_shifts", 0))

    lines = []
    lines.append(f"{date}의 근무는 {shift} ({stype}) 입니다.")
    if stype == "OFF":
        lines.append("이 날은 OFF로, 회복에 집중할 수 있는 날입니다.")
    else:
        lines.append(f"이 날의 overall risk 점수는 {risk}점으로, {level} 수준입니다.")

    if cw >= 3:
        lines.append(f"{cw}일 연속 근무 중이며, 피로 누적 가능성이 있습니다.")
    if cn >= 2:
        lines.append(f"{cn}일 연속 야간 근무가 이어지고 있습니다.")

    if row.get("weekend_flag"):
        lines.append("주말 근무에 해당합니다.")

    return "\n".join(lines)


def main():
    st.title("일별 스케줄 리포트")

    df = st.session_state.get("schedule_df")
    if df is None:
        st.warning("메인 페이지에서 먼저 스케줄 파일을 업로드해 주세요.")
        return

    nurse_list = st.session_state.get("nurse_list") or sorted(df["nurse_name"].dropna().unique().tolist())
    nurse_name = st.selectbox("간호사 선택", options=nurse_list)

    # 날짜 선택 (데이터 범위 기반)
    nurse_df = df[df["nurse_name"] == nurse_name]
    if nurse_df.empty:
        st.info("선택한 간호사의 스케줄이 없습니다.")
        return

    min_date = nurse_df["date"].min()
    max_date = nurse_df["date"].max()

    date = st.date_input("날짜 선택", value=max_date, min_value=min_date, max_value=max_date)

    day_row = nurse_df[nurse_df["date"] == date]
    if day_row.empty:
        st.info("해당 날짜에 스케줄이 없습니다.")
        return

    row = day_row.iloc[0]

    st.subheader("1. 요약 해설")
    st.markdown(generate_daily_summary(row))

    st.subheader("2. 전후 7일 스케줄 컨텍스트")
    start = date - dt.timedelta(days=7)
    end = date + dt.timedelta(days=7)
    ctx = nurse_df[(nurse_df["date"] >= start) & (nurse_df["date"] <= end)].sort_values("date")
    st.dataframe(ctx)


if __name__ == "__main__":
    main()

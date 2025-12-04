import streamlit as st

from utils.features import get_date_range_from_keyword, filter_schedule
from utils.risk import risk_level
from utils.fairness import compute_fairness_table, generate_fairness_narrative


# ------------------------------------------------
# INITIALIZE CHAT STATE
# ------------------------------------------------
def init_state():
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []


# ------------------------------------------------
# SAFETY SUMMARY
# ------------------------------------------------
def summarize_safety(df_slice, nurse_name, start, end) -> str:
    if df_slice.empty:
        return f"{nurse_name}님의 {start} ~ {end} 기간 스케줄이 없습니다."

    n_work = (df_slice["shift_type"] != "OFF").sum()
    n_night = (df_slice["shift_type"] == "NIGHT").sum()
    n_ed = df_slice["ED_quick_return"].sum()
    n_nq = df_slice["N_quick_return"].sum()
    max_cw = df_slice["consecutive_working_days"].max()
    max_cn = df_slice["consecutive_night_shifts"].max()
    avg_risk = df_slice["overall_risk_score"].mean()
    max_risk = df_slice["overall_risk_score"].max()
    level = risk_level(int(round(max_risk)))

    lines = [
        f"### {nurse_name}님의 {start} ~ {end} 환자안전·피로도 요약",
        f"- 근무일수(OFF 제외): **{int(n_work)}일**, 야간: **{int(n_night)}회**",
        f"- 최대 연속 근무일수: **{int(max_cw)}일**, 최대 연속 야간: **{int(max_cn)}일**",
    ]

    if n_ed > 0 or n_nq > 0:
        lines.append(
            f"- Quick return 패턴: ED {int(n_ed)}회, ND 계열 {int(n_nq)}회 "
            "(Critical risk 패턴)"
        )
    else:
        lines.append("- Quick return 패턴은 관찰되지 않았습니다.")

    lines.append(
        f"- 평균 위험도 점수: **{avg_risk:.2f}**, 최고점수: **{max_risk:.0f}** (위험수준: **{level}**)"
    )
    lines.append(
        "> 위험도 점수는 네가 정의한 엑셀 로직 기반의 합성 점수이며, 실제 적용 시 보정·검증이 필요합니다."
    )

    return "\n".join(lines)


# ------------------------------------------------
# MESSAGE HANDLER
# ------------------------------------------------
def handle_message(msg: str, df, nurse_name: str) -> str:
    msg = msg.strip()
    if not msg:
        return "입력된 내용이 없습니다."

    if df is None or df.empty:
        return "먼저 스케줄 파일을 업로드해 주세요."

    # 기간 추출
    start, end = get_date_range_from_keyword(msg)
    sub = filter_schedule(df[df["nurse_name"] == nurse_name])

    # 선택 기간 필터링
    sub = sub[(sub["date"] >= start) & (sub["date"] <= end)]

    if sub.empty:
        return f"{nurse_name}님의 {start} ~ {end} 기간 스케줄이 없습니다."

    # --------------------------------
    # 오늘/내일 근무
    # --------------------------------
    if "근무" in msg and ("오늘" in msg or "내일" in msg):
        row = sub.sort_values("date").iloc[0]
        return (
            f"{nurse_name}님의 {row['date']} 근무는 "
            f"**{row['shift_code']} ({row['shift_type']})** 입니다."
        )

    # --------------------------------
    # 야간 횟수
    # --------------------------------
    if ("야간" in msg or "night" in msg.lower()) and any(k in msg for k in ["몇", "개", "횟수"]):
        n_night = (sub["shift_type"] == "NIGHT").sum()
        return f"{nurse_name}님의 {start} ~ {end} 기간 야간 근무는 {int(n_night)}회입니다."

    # --------------------------------
    # 주말 횟수
    # --------------------------------
    if "주말" in msg and any(k in msg for k in ["몇", "개", "횟수"]):
        n_weekend = ((sub["shift_type"] != "OFF") & (sub["weekend_flag"])).sum()
        return f"{nurse_name}님의 {start} ~ {end} 기간 주말 근무는 {int(n_weekend)}회입니다."

    # --------------------------------
    # 위험도/피로도
    # --------------------------------
    if ("위험도" in msg) or ("피로도" in msg) or ("환자안전" in msg) or ("quick" in msg.lower()):
        return summarize_safety(sub, nurse_name, start, end)

    # --------------------------------
    # 연속 야간
    # --------------------------------
    if "연속" in msg and "야간" in msg:
        max_cn = sub["consecutive_night_shifts"].max()
        return f"{nurse_name}님의 최대 연속 야간 근무는 {int(max_cn)}일입니다."

    # --------------------------------
    # 연속 근무
    # --------------------------------
    if "연속" in msg and ("근무" in msg or "일수" in msg):
        max_cw = sub["consecutive_working_days"].max()
        return f"{nurse_name}님의 최대 연속 근무일수는 {int(max_cw)}일입니다."

    # --------------------------------
    # 공정성
    # --------------------------------
    if "공정성" in msg or "공평" in msg:
        summary = compute_fairness_table(df)
        return generate_fairness_narrative(summary, nurse_name)

    # --------------------------------
    # 기본 요약 (fallback)
    # --------------------------------
    sub_sorted = sub.sort_values("overall_risk_score", ascending=False)
    top = sub_sorted.iloc[0]
    level = risk_level(int(top["overall_risk_score"]))

    return (
        f"### {nurse_name}님의 {start} ~ {end} 근무 요약\n"
        f"- 근무일수: {int((sub['shift_type'] != 'OFF').sum())}일\n"
        f"- 야간 근무: {int((sub['shift_type'] == 'NIGHT').sum())}회\n"
        f"- 평균 위험도 점수: {sub['overall_risk_score'].mean():.2f}\n"
        f"- 가장 위험도가 높은 날: {top['date']} "
        f"(근무 {top['shift_code']} / 위험도 {top['overall_risk_score']:.0f}, 수준 {level})"
    )


# ------------------------------------------------
# PAGE UI
# ------------------------------------------------
def main():
    st.title("간호사 스케줄 챗봇")

    init_state()

    nurse_name = st.text_input("조회할 간호사 이름 입력")
    message = st.text_input("질문을 입력하세요")

    df = st.session_state.get("schedule_df", None)

    if st.button("질문하기"):
        answer = handle_message(message, df, nurse_name)
        st.write(answer)


if __name__ == "__main__":
    main()

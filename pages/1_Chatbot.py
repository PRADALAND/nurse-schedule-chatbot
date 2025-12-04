import streamlit as st
import pandas as pd
import datetime as dt

from utils.features import get_date_range_from_keyword, filter_schedule
from utils.risk import risk_level
from utils.fairness import compute_fairness_table, generate_fairness_narrative


def init_state():
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []


def generate_answer(message: str, df: pd.DataFrame, nurse_name: str) -> str:
    msg = message.strip()
    if not msg:
        return "질문을 이해하지 못했습니다. 다시 입력해 주세요."

    if df is None or df.empty:
        return "먼저 메인 페이지에서 스케줄 파일을 업로드해 주세요."

    # 기간 해석
    start, end = get_date_range_from_keyword(msg)
    sub = filter_schedule(df, nurse_name, start, end)

    if sub.empty:
        return f"{nurse_name}님의 {start} ~ {end} 기간 스케줄이 없습니다."

    # 1. 오늘/내일 근무
    if "근무" in msg and ("오늘" in msg or "내일" in msg):
        row = sub.sort_values("date").iloc[0]
        return (
            f"{nurse_name}님의 {row['date']} 근무는 "
            f"{row['shift_code']} ({row['shift_type']}) 입니다."
        )

    # 2. 야간/주말 횟수
    if ("야간" in msg or "night" in msg.lower()) and any(k in msg for k in ["몇", "개", "횟수"]):
        n_night = (sub["shift_type"] == "NIGHT").sum()
        return (
            f"{nurse_name}님의 {start} ~ {end} 기간 야간 근무는 총 {int(n_night)}회입니다."
        )

    if "주말" in msg and any(k in msg for k in ["몇", "개", "횟수"]):
        n_weekend = ((sub["shift_type"] != "OFF") & (sub["weekend_flag"])).sum()
        return (
            f"{nurse_name}님의 {start} ~ {end} 기간 주말 근무는 총 {int(n_weekend)}회입니다."
        )

    # 3. 위험도/피로도
    if ("위험도" in msg) or ("피로도" in msg):
        avg_risk = sub["overall_risk_score"].mean()
        max_risk = sub["overall_risk_score"].max()
        level = risk_level(int(round(max_risk)))
        n_night = (sub["shift_type"] == "NIGHT").sum()
        n_work = (sub["shift_type"] != "OFF").sum()

        return (
            f"{nurse_name}님의 {start} ~ {end} 기간 스케줄 위험도 요약입니다.\n"
            f"- 총 근무일수(OFF 제외): {int(n_work)}일\n"
            f"- 야간 근무: {int(n_night)}회\n"
            f"- 평균 overall risk 점수: {avg_risk:.2f}\n"
            f"- 최대 overall risk 점수: {max_risk:.0f} (위험 수준: {level})\n\n"
            f"※ 위험도 점수는 현재 예시 규칙 기반으로 계산되며, 실제 임상 근거 기반 모델로 교체가 필요합니다."
        )

    # 4. 공정성 질문
    if "공정성" in msg or "공평" in msg:
        summary = compute_fairness_table(df)
        return generate_fairness_narrative(summary, nurse_name)

    # 5. 기본 요약
    sub_sorted = sub.sort_values("overall_risk_score", ascending=False)
    top = sub_sorted.iloc[0]
    level = risk_level(int(top["overall_risk_score"]))

    return (
        f"{nurse_name}님의 {start} ~ {end} 기간 스케줄을 요약했습니다.\n"
        f"- 총 근무일수(OFF 제외): {int((sub['shift_type'] != 'OFF').sum())}일\n"
        f"- 야간 근무: {int((sub['shift_type'] == 'NIGHT').sum())}회\n"
        f"- 평균 overall risk 점수: {sub['overall_risk_score'].mean():.2f}\n"
        f"- 가장 위험도가 높은 날: {top['date']} "
        f"(근무 {top['shift_code']} / risk {top['overall_risk_score']:.0f}, 수준 {level})\n\n"
        f"보다 구체적으로 알고 싶은 내용(예: '이번주 야간 몇 번이야?', "
        f"'이번달 위험도 알려줘', '공정성은 어때?')를 물어보면 세부 내용을 설명해 드립니다."
    )


def main():
    st.title("스케줄 챗봇")

    df = st.session_state.get("schedule_df")
    if df is None:
        st.warning("메인 페이지에서 먼저 스케줄 파일을 업로드해 주세요.")
        return

    nurse_list = st.session_state.get("nurse_list") or sorted(df["nurse_name"].dropna().unique().tolist())
    nurse_name = st.selectbox("대상 간호사 선택", options=nurse_list)

    init_state()

    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("스케줄/위험도/공정성에 대해 질문해 보세요.")
    if user_input:
        st.session_state["chat_messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        answer = generate_answer(user_input, df, nurse_name)
        st.session_state["chat_messages"].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)


if __name__ == "__main__":
    main()

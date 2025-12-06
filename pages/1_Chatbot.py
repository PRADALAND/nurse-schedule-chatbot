import streamlit as st

from utils.features import (
    get_date_range_from_keyword,
    filter_schedule,
    compute_longest_work_streak,
    compute_longest_night_streak,
    find_peak_risk_info,
    date_in_range,
)
from utils.risk import risk_level
from utils.fairness import compute_fairness_table, generate_fairness_narrative


PRESET_QUESTIONS = {
    "이번 달 내 근무 위험도 요약": "이번달 내 근무 위험도 요약해줘",
    "이번 달 야간/주말 근무 횟수": "이번달 야간, 주말 근무 횟수 알려줘",
    "이번 달 최장 연속근무/연속야간": "이번달 최대 연속 근무일수와 연속야간 알려줘",
    "이번 달 quick return": "이번달 quick return 패턴과 횟수 알려줘",
}


# ------------------------------------------------
# INITIALIZE
# ------------------------------------------------
def init_state():
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []


# ------------------------------------------------
# SAFETY SUMMARY
# ------------------------------------------------
def summarize_safety(df_slice, nurse_name, start, end):

    if df_slice.empty:
        return f"{nurse_name}님의 {start} ~ {end} 기간 스케줄이 없습니다."

    n_work = (df_slice["shift_type"] != "OFF").sum()
    n_night = (df_slice["shift_type"] == "NIGHT").sum()
    n_ed = df_slice["ED_quick_return"].sum()
    n_nq = df_slice["N_quick_return"].sum()

    avg_risk = df_slice["overall_risk_score"].mean()
    max_risk = df_slice["overall_risk_score"].max()
    level = risk_level(int(max_risk))

    nurse_id = df_slice.iloc[0]["nurse_id"]

    cw_len, cw_start, cw_end = compute_longest_work_streak(df_slice, nurse_id)
    cn_len, cn_start, cn_end = compute_longest_night_streak(df_slice, nurse_id)

    peak = find_peak_risk_info(df_slice, nurse_id)
    if peak:
        if date_in_range(peak["date"], cw_start, cw_end):
            peak_line = (
                f"- 최고 위험도 날짜: **{peak['date']}** (근무 {peak['shift_code']}) → "
                f"연속근무 {cw_len}일 구간 내부"
            )
        else:
            peak_line = f"- 최고 위험도 날짜: **{peak['date']}** (근무 {peak['shift_code']})"
    else:
        peak_line = ""

    lines = [
        f"### {nurse_name}님의 {start} ~ {end} 위험 요약",
        f"- 근무일수: **{int(n_work)}일**, 야간: **{int(n_night)}회**",
        f"- 평균 위험점수: **{avg_risk:.2f}**, 최고점수: **{max_risk:.0f}** (수준: {level})",
    ]

    if cw_len > 1:
        lines.append(f"- 최장 연속근무: **{cw_len}일** ({cw_start} ~ {cw_end})")
    else:
        lines.append("- 연속근무 패턴 없음")

    if cn_len > 1:
        lines.append(f"- 최장 연속야간: **{cn_len}일** ({cn_start} ~ {cn_end})")
    else:
        lines.append("- 연속 야간근무 없음")

    if n_ed > 0 or n_nq > 0:
        lines.append(f"- Quick return: ED {n_ed}회, ND {n_nq}회")
    else:
        lines.append("- Quick return 없음")

    if peak_line:
        lines.append(peak_line)

    return "\n".join(lines)


# ------------------------------------------------
# MESSAGE HANDLER
# ------------------------------------------------
def handle_message(msg, df, nurse_name):

    msg = msg.strip()
    if not msg:
        return "질문을 입력해주세요."

    start, end = get_date_range_from_keyword(msg)
    sub = filter_schedule(df, nurse_name, start, end)

    if sub.empty:
        return f"{nurse_name}님의 {start} ~ {end} 스케줄이 없습니다."

    # today / tomorrow
    if "근무" in msg and ("오늘" in msg or "내일" in msg):
        row = sub.sort_values("date").iloc[0]
        return f"{row['date']} 근무는 **{row['shift_code']} ({row['shift_type']})** 입니다."

    # night count
    if "야간" in msg and any(k in msg for k in ["몇", "개", "횟수"]):
        return f"야간 근무는 {(sub['shift_type']=='NIGHT').sum()}회입니다."

    # weekend
    if "주말" in msg and any(k in msg for k in ["몇", "개", "횟수"]):
        cnt = ((sub["shift_type"] != "OFF") & sub["weekend_flag"]).sum()
        return f"주말 근무는 {cnt}회입니다."

    # risk-related
    if any(k in msg for k in ["위험", "피로", "안전", "quick", "연속"]):
        return summarize_safety(sub, nurse_name, start, end)

    # fairness
    if "공정성" in msg or "공평" in msg:
        summary = compute_fairness_table(df)
        return generate_fairness_narrative(summary, nurse_name)

    # fallback
    worst = sub.sort_values("overall_risk_score", ascending=False).iloc[0]
    level = risk_level(int(worst["overall_risk_score"]))

    return (
        f"- 근무일수: {(sub['shift_type']!='OFF').sum()}일\n"
        f"- 야간: {(sub['shift_type']=='NIGHT').sum()}회\n"
        f"- 평균 위험점수: {sub['overall_risk_score'].mean():.2f}\n"
        f"- 가장 위험한 날: {worst['date']} ({worst['shift_code']} / 수준 {level})"
    )


# ------------------------------------------------
# UI
# ------------------------------------------------
def main():
    st.title("간호사 스케줄 챗봇")

    init_state()

    # ---- FIX: schedule_df 없으면 안내 메시지 출력하고 종료 ----
    if "schedule_df" not in st.session_state or st.session_state["schedule_df"] is None:
        st.error("먼저 왼쪽 메뉴에서 스케줄 파일을 업로드해 주세요.")
        st.stop()

    df = st.session_state["schedule_df"]

    nurse_name = st.text_input("조회할 간호사 이름 입력")

    st.markdown("#### 1) 자주 쓰는 질문 바로 선택")
    cols = st.columns(2)

    preset_clicked = None
    for i, (label, q) in enumerate(PRESET_QUESTIONS.items()):
        if cols[i % 2].button(label):
            preset_clicked = q

    st.markdown("#### 2) 자유 질문 입력")
    message = st.text_input("예: '이번달 야간 몇 번이야?'")

    if preset_clicked:
        st.markdown(f"**Q:** {preset_clicked}")
        st.write(handle_message(preset_clicked, df, nurse_name))

    elif st.button("질문하기"):
        st.markdown(f"**Q:** {message}")
        st.write(handle_message(message, df, nurse_name))


if __name__ == "__main__":
    main()

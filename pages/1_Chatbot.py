import streamlit as st

from utils.features import get_date_range_from_keyword, filter_schedule
from utils.risk import risk_level
# 공정성 분석을 아직 안 쓰고 있다면 아래 두 줄은 주석 처리해도 됨.
from utils.fairness import compute_fairness_table, generate_fairness_narrative


def init_state():
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []


def _summarize_patient_safety(df_slice, nurse_name, start, end) -> str:
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

    lines = []
    lines.append(f"{nurse_name}님의 {start} ~ {end} 기간 환자안전·피로도 요약입니다.")
    lines.append(f"- 근무일수(OFF 제외): {int(n_work)}일, 야간 근무: {int(n_night)}회")
    lines.append(f"- 최대 연속 근무일수: {int(max_cw)}일, 최대 연속 야간: {int(max_cn)}일")

    if n_ed > 0 or n_nq > 0:
        lines.append(
            f"- Quick return 패턴: ED {int(n_ed)}회, ND 계열 {int(n_nq)}회 "
            "(엑셀 기준상 Critical risk 패턴으로 간주)"
        )
    else:
        lines.append("- Quick return 패턴은 관찰되지 않았습니다.")

    lines.append(
        f"- 평균 overall risk 점수: {avg_risk:.2f}, 최대 점수: {max_risk:.0f} (위험 수준: {level})"
    )
    lines.append(
        "※ 위험도 점수는 너가 설계한 엑셀 기준(연속근무/연속야간/quick return/인력부족)을 "
        "코드로 옮긴 값이며, 실제 연구·서비스 사용 시 추가 검증이 필요합니다."
    )
    return "\n".join(lines)


def generate_answer(message: str, df, nurse_name: str) -> str:
    msg = message.strip()
    if not msg:
        return "질문을 이해하지 못했습니다. 다시 입력해 주세요."

    if df is None or df.empty:
        return "먼저 메인 페이지에서 스케줄 파일을 업로드해 주세요."

    start, end = get_date_range_from_keyword(msg)
    sub = filter_schedule(df, nurse_name, start, end)

    if sub.empty:
        return f"{nurse_name}님의 {start} ~ {end} 기간 스케줄이 없습니다."

    # 1) 오늘/내일 근무
    if "근무" in msg and ("오늘" in msg or "내일" in msg):
        row = sub.sort_values("date").iloc[0]
        return (
            f"{nurse_name}님의 {row['date']} 근무는 "
            f"{row['shift_code']} ({row['shift_type']}) 입니다."
        )

    # 2) 야간/주말 횟수
    if ("야간" in msg or "night" in msg.lower()) and any(k in msg for k in ["몇", "개", "횟수"]):
        n_night = (sub["shift_type"] == "NIGHT").sum()
        return f"{nurse_name}님의 {start} ~ {end} 기간 야간 근무는 총 {int(n_night)}회입니다."

    if "주말" in msg and any(k in msg for k in ["몇", "개", "횟수"]):
        n_weekend = ((sub["shift_type"] != "OFF") & (sub["weekend_flag"])).sum()
        return f"{nurse_name}님의 {start} ~ {end} 기간 주말 근무는 총 {int(n_weekend)}회입니다."

    # 3) 위험도/피로도/환자안전/quick return 질문
    if ("위험도" in msg) or ("피로도" in msg) or ("환자안전" in msg) or ("quick" in msg.lower()):
        return _summarize_patient_safety(sub, nurse_name, start, end)

    if "연속" in msg and "야간" in msg:
        max_cn = sub["consecutive_night_shifts"].max()
        return f"{nurse_name}님의 {start} ~ {end} 기간 최대 연속 야간 근무는 {int(max_cn)}일입니다."

    if "연속" in msg and ("근무" in msg or "일수" in msg):
        max_cw = sub["consecutive_working_days"].max()
        return f"{nurse_name}님의 {start} ~ {end} 기간 최대 연속 근무일수는 {int(max_cw)}일입니다."

    # 4) 공정성 관련 질문 (fairness 모듈이 있을 때만 정상 동작)
    if "공정성" in msg or "공평" in msg:
        summary = compute_fairness_table(df)
        return generate_fairness_narrative(summary, nurse_name)

    # 5) 기본 요약
    sub_sorted = sub.sort_values("overall_risk_score", ascending=False)
    top = sub_sorted.iloc[0]
    level = risk_level(int(top["overall_risk_score"]))

    return (
        f"{nurse_name}님의 {start} ~ {end} 기간 스케줄을 요약했습니다.\n"
        f"- 근무일수(OFF 제외): {int((sub['shift_type'] != 'OFF').sum())}일\n"
        f"- 야간 근무: {int((sub['shift_type'] == 'NIGHT').sum())}회\n"
        f"- 평균 overall risk 점수: {sub['overall_risk_score'].mean():.2f}\n"
        f"- 가장 위험도가 높은 날: {top['date']} "
        f"(근무 {top['shift_code']} / ri_]()

import streamlit as st
import pandas as pd

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

from utils.file_store import upload_file
from utils.analysis_log import log_analysis
from utils.free_ai import analyze_csv_free, analyze_image_free   # 무료 AI

# =========================
# 프리셋 질문
# =========================
PRESET_QUESTIONS = {
    "이번 달 위험도 요약": "이번달 내 근무 위험도 요약해줘",
    "이번 달 야간/주말 횟수": "이번달 야간, 주말 근무 횟수 알려줘",
    "이번 달 최장 연속근무": "이번달 최대 연속 근무일수와 연속야간 알려줘",
    "이번 달 quick return": "이번달 quick return 패턴과 횟수 알려줘",
}


# =========================
# 위험 요약 함수
# =========================
def summarize_safety(df_slice, nurse_name, start, end):
    if df_slice.empty:
        return f"{start}~{end} 스케줄이 없습니다."

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
            peak_line = f"- 최고 위험일: **{peak['date']}** (연속근무 {cw_len}일 구간 내부)"
        else:
            peak_line = f"- 최고 위험일: **{peak['date']}**"
    else:
        peak_line = ""

    lines = [
        f"### {nurse_name}님의 {start}~{end} 위험요약",
        f"- 근무일수: **{n_work}일**, 야간 **{n_night}회**",
        f"- 평균 위험점수: **{avg_risk:.2f}**, 최고점수: **{max_risk:.0f}** ({level})",
        f"- 최장 연속근무: **{cw_len}일** ({cw_start}~{cw_end})" if cw_len > 1 else "- 연속근무 없음",
        f"- 최장 연속야간: **{cn_len}일** ({cn_start}~{cn_end})" if cn_len > 1 else "- 연속야간 없음",
        f"- Quick return: ED {n_ed}회, ND {n_nq}회" if (n_ed + n_nq) > 0 else "- Quick return 없음",
    ]

    if peak_line:
        lines.append(peak_line)

    return "\n".join(lines)


# =========================
# 자연어 메시지 핸들링
# =========================
def handle_message(msg, df, nurse_name):
    msg = msg.strip()
    if not msg:
        return "질문을 입력해주세요."

    start, end = get_date_range_from_keyword(msg)
    sub = filter_schedule(df, nurse_name, start, end)

    if sub.empty:
        return f"{start}~{end} 스케줄 없음."

    # 오늘/내일 근무
    if "근무" in msg and ("오늘" in msg or "내일" in msg):
        row = sub.sort_values("date").iloc[0]
        return f"{row['date']} 근무는 **{row['shift_code']}({row['shift_type']})** 입니다."

    # 야간 횟수
    if "야간" in msg and any(k in msg for k in ["몇", "개", "횟수"]):
        return f"야간 근무는 {(sub['shift_type']=='NIGHT').sum()}회입니다."

    # 주말 근무
    if "주말" in msg and any(k in msg for k in ["몇", "개", "횟수"]):
        cnt = ((sub["shift_type"] != "OFF") & sub["weekend_flag"]).sum()
        return f"주말 근무는 {cnt}회입니다."

    # 위험/피로/연속근무 관련
    if any(k in msg for k in ["위험", "피로", "안전", "quick", "연속"]):
        return summarize_safety(sub, nurse_name, start, end)

    # 공정성
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
        f"- 가장 위험한 날: {worst['date']} ({level})"
    )


# =========================
# 메인 UI
# =========================
def main():
    st.title("간호사 스케줄 챗봇")

    if "schedule_df" not in st.session_state or st.session_state["schedule_df"] is None:
        st.error("먼저 홈 화면에서 스케줄 파일을 업로드하세요.")
        st.stop()

    df = st.session_state["schedule_df"]
    nurse_name = st.text_input("조회할 간호사 이름")

    # 1) 프리셋 질문
    st.markdown("### 1) 자주 쓰는 질문")
    cols = st.columns(2)
    preset_clicked = None

    for i, (label, q) in enumerate(PRESET_QUESTIONS.items()):
        if cols[i % 2].button(label):
            preset_clicked = q

    # 2) 자유 질문
    st.markdown("### 2) 자유 질문 입력")
    message = st.text_input("예: '이번달 야간 몇 번?'")

    if preset_clicked:
        st.markdown(f"**Q:** {preset_clicked}")
        st.write(handle_message(preset_clicked, df, nurse_name))

    elif st.button("질문하기"):
        st.markdown(f"**Q:** {message}")
        st.write(handle_message(message, df, nurse_name))

    # -----------------------------
    # 3) 무료 AI 분석 기능
    # -----------------------------
    st.markdown("---")
    st.markdown("### 3) AI 파일 분석 (무료 모델 사용)")

    ai_file = st.file_uploader(
        "이미지 또는 CSV 업로드",
        type=["csv", "png", "jpg", "jpeg"],
        key="ai_file_uploader",
    )

    ai_prompt = st.text_area(
        "분석 요청",
        placeholder="예: 이 CSV의 위험 패턴 요약해줘 / 이미지 설명해줘",
        key="ai_prompt",
    )

    run_ai = st.button(
        "AI 분석 실행 (무료 모델)",
        disabled=(ai_file is None or not ai_prompt.strip()),
    )

    if run_ai:
        with st.spinner("무료 AI 모델로 분석 중..."):

            user_id = nurse_name if nurse_name else "anon"
            path, url = upload_file(user_id, ai_file)
            fname = ai_file.name.lower()

            if fname.endswith(".csv"):
                ai_file.seek(0)
                df_uploaded = pd.read_csv(ai_file)
                ai_summary = analyze_csv_free(df_uploaded, ai_prompt)
                file_type = "csv"

            else:
                ai_file.seek(0)
                image_bytes = ai_file.read()
                ai_summary = analyze_image_free(image_bytes, ai_prompt)
                file_type = "image"

            # 로그 저장
            log_analysis(
                user_id=user_id,
                file_name=ai_file.name,
                file_type=file_type,
                file_url=url,
                user_prompt=ai_prompt,
                ai_summary=ai_summary,
            )

        st.success("AI 분석 완료 (무료 모델)")
        st.write(ai_summary)

        if file_type == "csv":
            st.markdown("#### CSV 미리보기")
            st.dataframe(df_uploaded.head(20))

        else:
            st.markdown("#### 이미지 미리보기")
            st.image(url)


if __name__ == "__main__":
    main()

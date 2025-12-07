import streamlit as st
import pandas as pd

from openai import OpenAI

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

# OpenAI 클라이언트 (환경변수 OPENAI_API_KEY 사용)
client = OpenAI()

PRESET_QUESTIONS = {
    "이번 달 위험도 요약": "이번달 내 근무 위험도 요약해줘",
    "이번 달 야간/주말 횟수": "이번달 야간, 주말 근무 횟수 알려줘",
    "이번 달 최장 연속근무": "이번달 최대 연속 근무일수와 연속야간 알려줘",
    "이번 달 quick return": "이번달 quick return 패턴과 횟수 알려줘",
}


def init_state():
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []


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


def handle_message(msg, df, nurse_name):
    msg = msg.strip()
    if not msg:
        return "질문을 입력해주세요."

    start, end = get_date_range_from_keyword(msg)
    sub = filter_schedule(df, nurse_name, start, end)

    if sub.empty:
        return f"{start}~{end} 스케줄 없음."

    # Today / Tomorrow
    if "근무" in msg and ("오늘" in msg or "내일" in msg):
        row = sub.sort_values("date").iloc[0]
        return f"{row['date']} 근무는 **{row['shift_code']}({row['shift_type']})** 입니다."

    # Night count
    if "야간" in msg and any(k in msg for k in ["몇", "개", "횟수"]):
        return f"야간 근무는 {(sub['shift_type']=='NIGHT').sum()}회입니다."

    # Weekend
    if "주말" in msg and any(k in msg for k in ["몇", "개", "횟수"]):
        cnt = ((sub["shift_type"] != "OFF") & sub["weekend_flag"]).sum()
        return f"주말 근무는 {cnt}회입니다."

    # Risk / fatigue
    if any(k in msg for k in ["위험", "피로", "안전", "quick", "연속"]):
        return summarize_safety(sub, nurse_name, start, end)

    # Fairness
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


def main():
    st.title("간호사 스케줄 챗봇")

    if "schedule_df" not in st.session_state or st.session_state["schedule_df"] is None:
        st.error("먼저 홈 화면에서 스케줄 파일을 업로드하세요.")
        st.stop()

    df = st.session_state["schedule_df"]

    nurse_name = st.text_input("조회할 간호사 이름")

    # -----------------------------
    # 1) 프리셋 질문
    # -----------------------------
    st.markdown("### 1) 자주 쓰는 질문")
    cols = st.columns(2)
    preset_clicked = None
    for i, (label, q) in enumerate(PRESET_QUESTIONS.items()):
        if cols[i % 2].button(label):
            preset_clicked = q

    # -----------------------------
    # 2) 자유 질문
    # -----------------------------
    st.markdown("### 2) 자유 질문 입력")
    message = st.text_input("예: '이번달 야간 몇 번?'")

    if preset_clicked:
        st.markdown(f"**Q:** {preset_clicked}")
        st.write(handle_message(preset_clicked, df, nurse_name))

    elif st.button("질문하기"):
        st.markdown(f"**Q:** {message}")
        st.write(handle_message(message, df, nurse_name))

    # -----------------------------
    # 3) AI 파일 분석 (이미지 · CSV)
    # -----------------------------
    st.markdown("---")
    st.markdown("### 3) AI 파일 분석 (이미지 · CSV)")

    ai_file = st.file_uploader(
        "이미지 또는 CSV 업로드",
        type=["csv", "png", "jpg", "jpeg"],
        key="ai_file_uploader",
    )
    ai_prompt = st.text_area(
        "분석 요청",
        placeholder="예: 이 CSV의 위험 패턴 요약해줘 / 이 이미지를 객관적으로 설명해줘",
        key="ai_prompt",
    )

    run_ai = st.button(
        "AI 분석 실행",
        disabled=(ai_file is None or not ai_prompt.strip()),
        key="ai_analyze_button",
    )

    if run_ai and ai_file is not None and ai_prompt.strip():
        with st.spinner("AI 분석 중..."):
            user_id = nurse_name if nurse_name else "anon"

            # 3-1) Supabase Storage 업로드
            path, url = upload_file(user_id, ai_file)

            fname = ai_file.name.lower()
            # 3-2) 파일 타입별 AI 분석
            if fname.endswith(".csv"):
                # upload_file에서 read()를 한 번 했으므로 다시 읽기 위해 포인터 리셋
                ai_file.seek(0)
                df_uploaded = pd.read_csv(ai_file)
                sample_csv = df_uploaded.head(20).to_csv(index=False)

                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a clinical data analyst specializing in "
                                "nurse scheduling, workload, fatigue risk, and safety patterns. "
                                "Explain results in clear Korean for nurses."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"사용자 분석 요청:\n{ai_prompt}\n\n"
                                f"다음은 CSV 상위 20행 미리보기입니다.\n"
                                f"{sample_csv}\n\n"
                                "간호사 입장에서 이해하기 쉬운 방식으로 "
                                "핵심 위험 패턴과 해석을 정리해 주세요."
                            ),
                        },
                    ],
                )
                ai_summary = completion.choices[0].message.content
                file_type = "csv"

            else:
                # 이미지 비전 분석
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "다음 이미지를 간호사/연구자의 관점에서 "
                                        "객관적으로 설명해 주세요.\n"
                                        f"사용자 분석 요청: {ai_prompt}"
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": url},
                                },
                            ],
                        }
                    ],
                )
                ai_summary = completion.choices[0].message.content
                file_type = "image"

            # 3-3) 분석 로그 DB 저장
            log_analysis(
                user_id=user_id,
                file_name=ai_file.name,
                file_type=file_type,
                file_url=url,
                user_prompt=ai_prompt,
                ai_summary=ai_summary,
            )

        st.success("AI 분석 완료")
        st.markdown("#### AI 분석 결과")
        st.write(ai_summary)

        if file_type == "csv":
            st.markdown("#### CSV 미리보기 (상위 20행)")
            st.dataframe(df_uploaded.head(20))
        else:
            st.markdown("#### 이미지 미리보기")
            st.image(url)


if __name__ == "__main__":
    main()

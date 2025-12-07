# pages/Chatbot.py

import streamlit as st
import pandas as pd
from utils.free_ai import call_llm
from utils.features import get_date_range_from_keyword

st.title("근무 스케줄 챗봇 (AI 기반)")

df = st.session_state.get("schedule_df")
if df is None:
    st.warning("스케줄 데이터가 없습니다. 메인 페이지에서 파일 업로드하세요.")
    st.stop()


# -----------------------------------------------------
# 통계 계산 함수 (최장연속근무 오류 보정)
# -----------------------------------------------------
def compute_stats(df_slice):
    stats = {}

    # 1) 개인 리스트
    names = df_slice["nurse_name"].unique()

    for name in names:
        sub = df_slice[df_slice["nurse_name"] == name].sort_values("date")

        # 전체 근무일수 (OFF 제외)
        workdays = (sub["shift_type"] != "OFF").sum()

        # 야간 횟수
        nights = (sub["shift_type"] == "NIGHT").sum()

        # 최장 연속 근무 계산
        max_streak = 0
        cur = 0
        prev_day = None

        for _, row in sub.iterrows():
            if row["shift_type"] != "OFF":
                if prev_day is None or (row["date"] - prev_day).days == 1:
                    cur += 1
                else:
                    cur = 1
                prev_day = row["date"]
            else:
                cur = 0
                prev_day = None

            max_streak = max(max_streak, cur)

        stats[name] = {
            "workdays": int(workdays),
            "nights": int(nights),
            "max_streak": int(max_streak),
        }

    return stats


# -----------------------------------------------------
# 대화 히스토리 관리
# -----------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# -----------------------------------------------------
# 사용자 입력
# -----------------------------------------------------
query = st.text_input("질문을 입력하세요:", placeholder="예: 이번달 야간 많이 한 사람 누구?")


if st.button("분석 요청"):
    if not query.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    # 날짜 범위 해석
    start, end = get_date_range_from_keyword(query)
    df_slice = df[(df["date"] >= start) & (df["date"] <= end)]

    # 통계 계산
    stats = compute_stats(df_slice)

    # 텍스트 형태로 변환
    stats_text = "\n".join(
        f"- {name}: 근무일수 {v['workdays']}일, NIGHT {v['nights']}회, 최장연속근무 {v['max_streak']}일"
        for name, v in stats.items()
    )

    # ------------------------------
    # AI 프롬프트
    # ------------------------------
    prompt = f"""
아래는 병동 스케줄 통계이다. 이를 기반으로 질문에 답하라.

[질문]
{query}

[분석 기간]
{start} ~ {end}

[간호사별 통계]
{stats_text}

규칙:
1) 답변은 자연스러운 한국어로 최종 결과만 말한다.
2) 절대로 사고 과정, <think>, reasoning을 출력하지 않는다.
3) 같은 문장을 반복하지 않는다.
4) 주어진 통계를 기반으로 반드시 결론을 도출한다.
5) 가능하면 '가장 ~한 사람은 누구인지' 명확히 판단하라.
"""

    ai_answer = call_llm(prompt)

    # 기록
    st.session_state.chat_history.append((query, ai_answer))


# -----------------------------------------------------
# 히스토리 출력창 (대화형 UI)
# -----------------------------------------------------
st.markdown("### 대화 기록")
for q, a in st.session_state.chat_history:
    st.markdown(f"**사용자:** {q}")
    st.markdown(f"**AI:** {a}")
    st.markdown("---")

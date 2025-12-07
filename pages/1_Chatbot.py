import streamlit as st
import pandas as pd
from utils.features import get_date_range_from_keyword
from utils.analysis_log import log_analysis
from utils.free_ai import call_llm

st.title("근무 스케줄 챗봇 (AI 기반)")

# 스케줄 데이터 로드
df = st.session_state.get("schedule_df", None)
if df is None:
    st.warning("스케줄 데이터가 없습니다. 메인 페이지에서 파일 업로드하세요.")
    st.stop()

# ----------------------------
# 대화 세션 초기화
# ----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # 완전 비어 있는 상태로 시작


# ----------------------------
# 사용자 입력
# ----------------------------
query = st.text_input(
    "질문을 입력하세요:",
    placeholder="예: '홍길동 이번달 야간 몇 번?'"
)

if st.button("분석 요청"):
    if not query.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    # 날짜 범위 파싱
    start, end = get_date_range_from_keyword(query)
    df_slice = df[(df["date"] >= start) & (df["date"] <= end)]

    # 자동 통계 요약
    total_work = int((df_slice["shift_type"] != "OFF").sum())
    night_count = int((df_slice["shift_type"] == "NIGHT").sum())

    auto_stats = (
        f"선택된 기간: {start} ~ {end}\n"
        f"전체 근무일수: {total_work}\n"
        f"야간 근무 횟수: {night_count}\n"
    )

    # ----------------------------
    # 대화형 LLM 프롬프트 구성
    # ----------------------------
    chat_messages = [
        {"role": "system", "content": (
            "너는 병동 스케줄 분석을 수행하는 한국어 AI이다. "
            "항상 한국어로 답변하고, 주어진 통계를 기반으로만 판단한다. "
            "사용자가 유도하지 않는 이상 과도한 설명, 전문 용어, 반복은 피하라."
        )}
    ]

    # 기존 대화 이력 추가
    for turn in st.session_state.chat_history:
        chat_messages.append(turn)

    # 이번 질문 추가
    chat_messages.append({"role": "user", "content": f"{query}\n\n[자동 통계]\n{auto_stats}"})

    # LLM 호출
    response = call_llm(chat_messages)

    # 대화 세션에 추가
    st.session_state.chat_history.append({"role": "user", "content": query})
    st.session_state.chat_history.append({"role": "assistant", "content": response})

    # 로그 저장
    log_analysis(query, response)


# ----------------------------
# 대화 이력 표시
# ----------------------------
st.subheader("대화 기록")

for turn in st.session_state.chat_history:
    role = "사용자" if turn["role"] == "user" else "AI"
    st.markdown(f"**{role}:** {turn['content']}")

import streamlit as st
import pandas as pd
from utils.features import get_date_range_from_keyword
from utils.analysis_log import log_analysis
from utils.free_ai import call_llm

st.title("근무 스케줄 챗봇 (AI 기반)")

# 스케줄 데이터 확인
df = st.session_state.get("schedule_df", None)
if df is None:
    st.warning("스케줄 데이터가 없습니다. 메인 페이지에서 파일을 업로드하세요.")
    st.stop()

# =====================================
# 세션 상태 초기화
# =====================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "recent_queries" not in st.session_state:
    st.session_state.recent_queries = []  # 최근 질문 5개 저장


# =====================================
# 추천 질문 (자동완성 역할)
# =====================================
default_suggestions = [
    "이번 달 야간 많이 한 사람 누구?",
    "홍길동 이번 달 OFF 몇 번?",
    "누가 이번 달 근무가 가장 빡셌어?",
    "이번 달 위험도 요약해줘",
    "연속 근무 많은 사람 알려줘"
]

st.subheader("추천 질문")
cols = st.columns(3)

for idx, q in enumerate(default_suggestions):
    with cols[idx % 3]:
        if st.button(q):
            st.session_state.pre_input = q  # 입력창 자동완성
            

# 최근 질문 추천
if st.session_state.recent_queries:
    st.subheader("최근에 했던 질문")
    cols2 = st.columns(3)

    for i, q in enumerate(st.session_state.recent_queries[-5:]):
        with cols2[i % 3]:
            if st.button(f"🔁 {q}"):
                st.session_state.pre_input = q


# =====================================
# 입력창 (자동완성 지원)
# =====================================
query = st.text_input(
    "질문을 입력하세요:",
    value=st.session_state.get("pre_input", ""),
    placeholder="예: '홍길동 이번달 야간 몇 번?'",
)

if st.button("분석 요청"):
    if not query.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    # 최근 질문 저장
    if query not in st.session_state.recent_queries:
        st.session_state.recent_queries.append(query)
        st.session_state.recent_queries = st.session_state.recent_queries[-5:]

    # 날짜 범위
    start, end = get_date_range_from_keyword(query)
    df_slice = df[(df["date"] >= start) & (df["date"] <= end)]

    total_work = int((df_slice["shift_type"] != "OFF").sum())
    night_count = int((df_slice["shift_type"] == "NIGHT").sum())

    auto_stats = (
        f"선택된 기간: {start} ~ {end}\n"
        f"전체 근무일수: {total_work}\n"
        f"야간 근무 횟수: {night_count}\n"
    )

    # 대화형 LLM 메시지 구성
    chat_messages = [{"role": "system", "content": (
        "너는 병동 스케줄 분석을 수행하는 한국어 AI이다. "
        "항상 한국어로 답변하고, 주어진 통계를 기반으로만 판단한다. "
        "중복, 반복, 장황한 설명을 하지 마라."
    )}]

    # 기존 대화 포함
    for turn in st.session_state.chat_history:
        chat_messages.append(turn)

    # 이번 질문 추가
    chat_messages.append({"role": "user", "content": f"{query}\n\n[자동 통계]\n{auto_stats}"})

    # LLM 호출
    ai_response = call_llm(chat_messages)

    # 히스토리 저장
    st.session_state.chat_history.append({"role": "user", "content": query})
    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

    # 로그 저장
    log_analysis(query, ai_response)

    # 입력창 초기화
    st.session_state.pre_input = ""


# =====================================
# 대화 UI: 말풍선 형태
# =====================================
st.subheader("대화 기록")

chat_css = """
<style>
.user-bubble {
    background-color: #D6EAFE;
    padding: 10px 15px;
    border-radius: 12px;
    max-width: 70%;
    margin-left: auto;
    margin-bottom: 10px;
}
.ai-bubble {
    background-color: #F1F0F0;
    padding: 10px 15px;
    border-radius: 12px;
    max-width: 70%;
    margin-right: auto;
    margin-bottom: 10px;
}
</style>
"""
st.markdown(chat_css, unsafe_allow_html=True)

for turn in st.session_state.chat_history:
    if turn["role"] == "user":
        st.markdown(f"<div class='user-bubble'><b>사용자:</b><br>{turn['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'><b>AI:</b><br>{turn['content']}</div>", unsafe_allow_html=True)

import streamlit as st
import pandas as pd

# ============================================================
# 안전한 utils import (없어도 앱이 죽지 않도록 처리)
# ============================================================
try:
    from utils.features import get_date_range_from_keyword
except Exception:
    def get_date_range_from_keyword(x):
        return None

try:
    from utils.analysis_log import log_analysis
except Exception:
    def log_analysis(*args, **kwargs):
        return None

try:
    from utils.free_ai import call_llm
except Exception:
    # utils.free_ai 없을 때 임시 LLM 함수
    def call_llm(prompt):
        return "AI 응답 테스트 중입니다. utils.free_ai가 없어서 임시 메시지를 반환합니다."
        

# ============================================================
# 초기 상태 설정
# ============================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "user_query" not in st.session_state:
    st.session_state.user_query = ""


# ============================================================
# 페이지 UI
# ============================================================
st.title("근무 스케줄 챗봇 (AI 기반)")

st.markdown("병동 스케줄을 기반으로 실제 간호사 분석 방식에 맞게 답변합니다.")


# ============================================================
# 최근 질문 추천 기능
# ============================================================
st.subheader("최근 많이 사용된 질문")

sample_queries = [
    "이번 달 N 비율 분석해줘",
    "A 간호사의 연속 야간근무 위험 알려줘",
    "주말 근무 분배 공정한지 평가해줘",
]

cols = st.columns(len(sample_queries))

for i, q in enumerate(sample_queries):
    if cols[i].button(q):
        st.session_state.user_query = q


# ============================================================
# 사용자 입력
# ============================================================
user_query = st.text_input(
    "질문을 입력하세요:",
    value=st.session_state.user_query,
    placeholder="예: 이번 달 A 간호사의 근무 패턴 분석해줘"
)

submit = st.button("전송")


# ============================================================
# 사용자 질문 처리
# ============================================================
if submit and user_query.strip():
    # 사용자 메시지 저장
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_query
    })

    # Prompt 생성
    prompt = f"""
너는 한국 병동에서 사용하는 '근무 스케줄 분석 AI'이다.

[사용자 질문]
{user_query}

간결하면서도 정확하게 답해라.
"""

    # LLM 호출
    ai_response = call_llm(prompt)

    # AI 메시지 저장
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": ai_response
    })

    st.session_state.user_query = ""


# ============================================================
# 말풍선 스타일 정의
# ============================================================
st.markdown("""
<style>
.user-bubble {
    background-color: #DCF8C6;
    padding: 10px 15px;
    border-radius: 12px;
    margin: 8px 0;
    width: fit-content;
    max-width: 80%;
}
.ai-bubble {
    background-color: #F1F0F0;
    padding: 10px 15px;
    border-radius: 12px;
    margin: 8px 0;
    width: fit-content;
    max-width: 80%;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# 채팅 렌더링
# ============================================================
st.subheader("대화 기록")

for turn in st.session_state.chat_history:
    role = turn["role"]
    text = turn.get("content", "")  # KeyError 방지

    if role == "user":
        st.markdown(
            f"<div class='user-bubble'><b>사용자</b><br>{text}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='ai-bubble'><b>AI</b><br>{text}</div>",
            unsafe_allow_html=True
        )

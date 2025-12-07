# pages/1_Chatbot.py

import streamlit as st
import pandas as pd

# ----------------------------------------------------
# 1) 세션 상태 초기화: 대화 기록 구조 강제
# ----------------------------------------------------
if "chat_history" not in st.session_state or not isinstance(st.session_state.chat_history, list):
    st.session_state.chat_history = []

# ----------------------------------------------------
# 2) utils 모듈 로드 (Cloud 경로 문제 대비)
# ----------------------------------------------------
try:
    from utils.features import get_date_range_from_keyword
    from utils.analysis_log import log_analysis
    from utils.free_ai import call_llm
except Exception as e:
    st.error(f"[ERROR] utils 모듈 로드에 실패했습니다: {e}")
    st.stop()

# ----------------------------------------------------
# 3) 페이지 헤더
# ----------------------------------------------------
st.title("근무 스케줄 챗봇 (AI 기반)")
st.write("간호사 근무표와 근무 스케줄에 대해 질문하면, 데이터 기반으로 해석을 도와드립니다.")

# ----------------------------------------------------
# 4) 사용자 입력 UI
# ----------------------------------------------------
query = st.text_input("질문을 입력하세요:", "")

if st.button("질문 보내기") and query.strip():

    user_text = query.strip()

    # 4-1) 사용자 메시지 세션에 저장
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_text,
    })

    # 4-2) (선택) 날짜 범위 파싱 – 나중에 스케줄 분석에 활용 가능
    try:
        date_info = get_date_range_from_keyword(user_text)
    except Exception:
        date_info = None

    # 4-3) LLM 호출 (프롬프트 제어는 free_ai.call_llm 내부에서 수행)
    answer = call_llm(user_text)

    # 4-4) AI 응답 저장
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer,
    })

    # 4-5) 분석 로그 저장 (예외는 무시)
    try:
        log_analysis(user_text, answer)
    except Exception:
        pass

# ----------------------------------------------------
# 5) 채팅 버블 CSS (다크 모드 가독성 최적화)
# ----------------------------------------------------
chat_css = """
<style>
.user-bubble {
    background-color: #d0e7ff;  /* 연한 파랑 */
    color: #0a0a0a;             /* 진한 글자색 */
    padding: 12px;
    border-radius: 10px;
    max-width: 85%;
    margin-bottom: 10px;
}

.ai-bubble {
    background-color: #fff4c2;  /* 연한 크림색 */
    color: #0a0a0a;             /* 진한 글자색 */
    padding: 12px;
    border-radius: 10px;
    max-width: 85%;
    margin-bottom: 10px;
}

.chat-wrapper {
    margin-top: 20px;
}
</style>
"""
st.markdown(chat_css, unsafe_allow_html=True)

# ----------------------------------------------------
# 6) 대화 기록 출력
# ----------------------------------------------------
st.subheader("대화 기록")
st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)

for turn in st.session_state.chat_history:

    # 혹시라도 과거 버전에서 tuple이 섞여 있으면 skip
    if not isinstance(turn, dict):
        continue

    role = turn.get("role", "")
    text = turn.get("content", "")

    if role == "user":
        st.markdown(
            f"<div class='user-bubble'><b>사용자:</b><br>{text}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='ai-bubble'><b>AI:</b><br>{text}</div>",
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

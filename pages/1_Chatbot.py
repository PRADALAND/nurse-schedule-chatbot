import streamlit as st
import pandas as pd

# ====== 안전 초기화 ===========================================================
# chat_history가 없거나, list가 아닌 경우 새로 초기화
if "chat_history" not in st.session_state or not isinstance(st.session_state.chat_history, list):
    st.session_state.chat_history = []

# utils 모듈 로드 (Cloud에서 에러 방지)
try:
    from utils.features import get_date_range_from_keyword
    from utils.analysis_log import log_analysis
    from utils.free_ai import call_llm
except Exception as e:
    st.error(f"[ERROR] utils 모듈 로드 실패: {e}")
    st.stop()

# ====== UI ====================================================================
st.title("근무 스케줄 챗봇 (AI 기반)")
st.write("한국 병동 근무표를 해석하고 데이터 기반 분석을 제공합니다.")

# 입력창
query = st.text_input("질문을 입력하세요:", "")

# ====== 사용자 입력 처리 =========================================================
if st.button("질문 보내기") and query.strip():

    # 사용자 turn 저장
    st.session_state.chat_history.append({
        "role": "user",
        "content": query.strip()
    })

    # 날짜 범위 추출 (오류 방지)
    try:
        date_info = get_date_range_from_keyword(query)
    except:
        date_info = None

    # 실제 LLM 호출
    try:
        llm_response = call_llm(query)
    except Exception as e:
        llm_response = f"[LLM 오류 발생] {e}"

    # AI 답변 저장
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": llm_response
    })

    # 로그 기록
    try:
        log_analysis(query, llm_response)
    except:
        pass

# ====== 대화 기록 UI용 CSS ======================================================
chat_css = """
<style>
.user-bubble {
    background-color: #e3f2fd;
    padding: 10px;
    border-radius: 10px;
    max-width: 80%;
    margin-bottom: 10px;
}
.ai-bubble {
    background-color: #fff3cd;
    padding: 10px;
    border-radius: 10px;
    max-width: 80%;
    margin-bottom: 10px;
}
</style>
"""
st.markdown(chat_css, unsafe_allow_html=True)

# ====== 대화 기록 출력 ===========================================================
st.subheader("대화 기록")

for turn in st.session_state.chat_history:

    # 깨진 tuple 등이 섞여 있다면 Skip
    if not isinstance(turn, dict):
        continue

    role = turn.get("role", "")
    text = turn.get("content", "")

    if role == "user":
        st.markdown(f"<div class='user-bubble'><b>사용자:</b><br>{text}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'><b>AI:</b><br>{text}</div>", unsafe_allow_html=True)

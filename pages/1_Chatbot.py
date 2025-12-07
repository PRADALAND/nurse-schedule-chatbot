import streamlit as st
import pandas as pd

# ============================================================
# 1) 안전한 상태 초기화
# ============================================================
if "chat_history" not in st.session_state or not isinstance(st.session_state.chat_history, list):
    st.session_state.chat_history = []

# ============================================================
# 2) utils 모듈 불러오기 (Cloud 경로 문제 대비)
# ============================================================
try:
    from utils.features import get_date_range_from_keyword
    from utils.analysis_log import log_analysis
    from utils.free_ai import call_llm
except Exception as e:
    st.error(f"[ERROR] utils 모듈 로드 실패: {e}")
    st.stop()

# ============================================================
# 3) 페이지 헤더
# ============================================================
st.title("근무 스케줄 챗봇 (AI 기반)")
st.write("간호사 근무표 분석과 질적 해석을 제공하는 한국어 기반 AI 입니다.")

# ============================================================
# 4) 유저 입력 UI
# ============================================================
query = st.text_input("질문을 입력하세요:", "")

if st.button("질문 보내기") and query.strip():

    # 4-1) 사용자 메시지 저장
    st.session_state.chat_history.append({
        "role": "user",
        "content": query.strip()
    })

    # 4-2) 날짜 범위 파싱
    try:
        date_info = get_date_range_from_keyword(query)
    except:
        date_info = None

    # 4-3) LLM 호출
    try:
        llm_response = call_llm(
            f"""
            아래 질문에 대해 한국어만 사용해서 답변하라.
            절대 한자(漢字), 일본어(かな), 중국어(汉字)를 사용하지 말고,
            모든 문장은 자연스러운 한국어로만 작성하라.

            질문: {query}
            """
        )
    except Exception as e:
        llm_response = f"[LLM 오류] {e}"

    # 4-4) AI 메시지 저장
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": llm_response
    })

    # 4-5) 로그 저장
    try:
        log_analysis(query, llm_response)
    except:
        pass

# ============================================================
# 5) 채팅 버블 CSS (가독성 최적화)
# ============================================================
chat_css = """
<style>
.user-bubble {
    background-color: #d0e7ff;  /* 연한 파랑 */
    color: #0a0a0a;             /* 글자 검정 */
    padding: 12px;
    border-radius: 10px;
    max-width: 85%;
    margin-bottom: 10px;
}

.ai-bubble {
    background-color: #fff4c2;  /* 연한 크림색 */
    color: #0a0a0a;             /* 글자 검정 */
    padding: 12px;
    border-radius: 10px;
    max-width: 85%;
    margin-bottom: 10px;
}

/* 대화 영역 간격 */
.chat-wrapper {
    margin-top: 20px;
}
</style>
"""
st.markdown(chat_css, unsafe_allow_html=True)

# ============================================================
# 6) 대화 기록 출력
# ============================================================
st.subheader("대화 기록")

st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)

for turn in st.session_state.chat_history:

    # 데이터가 tuple 등으로 깨졌으면 skip
    if not isinstance(turn, dict):
        continue

    role = turn.get("role", "")
    text = turn.get("content", "")

    if role == "user":
        st.markdown(
            f"<div class='user-bubble'><b>사용자:</b><br>{text}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='ai-bubble'><b>AI:</b><br>{text}</div>",
            unsafe_allow_html=True
        )

st.markdown("</div>", unsafe_allow_html=True)

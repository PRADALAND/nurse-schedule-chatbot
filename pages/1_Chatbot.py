import streamlit as st
from utils.free_ai import call_llm

bubble_css = """
<style>

.chat-container {
    margin-top: 10px;
}

/* 사용자 메시지 */
.user-bubble {
    background-color: #dce9f7;   /* 연한 하늘색 */
    color: #000000 !important;   /* 글자 검정 */
    padding: 12px 14px;
    border-radius: 12px;
    margin-bottom: 10px;
    font-size: 16px;
    line-height: 1.5;
    border: 1px solid #b9d3ea;
}

/* AI 메시지 */
.ai-bubble {
    background-color: #fff5cc;   /* 연한 크림색 */
    color: #000000 !important;   /* 글자 검정 */
    padding: 12px 14px;
    border-radius: 12px;
    margin-bottom: 10px;
    font-size: 16px;
    line-height: 1.5;
    border: 1px solid #e6dca8;
}

/* 역할 표시 텍스트(사용자:, AI:) */
.role-label {
    font-weight: 600;
    color: #333333 !important;
    margin-bottom: 4px;
    display: block;
}

</style>
"""
st.markdown(bubble_css, unsafe_allow_html=True)


st.set_page_config(page_title="근무 스케줄 챗봇", layout="wide")

# ==============================
# 세션 초기화 (오류 방지)
# ==============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 이전에 tuple 등이 있었으면 강제로 정리
cleaned = []
for item in st.session_state.chat_history:
    if isinstance(item, dict) and "role" in item and "content" in item:
        cleaned.append(item)
st.session_state.chat_history = cleaned


# ==============================
# 입력 UI
# ==============================
st.title("근무 스케줄 챗봇 (AI 기반)")
query = st.text_input("질문을 입력하세요.", key="ask_input")

if st.button("질문 보내기"):
    if query.strip():

        # 사용자 메시지 기록
        st.session_state.chat_history.append({
            "role": "user",
            "content": query.strip()
        })

        # LLM 호출
        answer = call_llm(query.strip())

        # AI 메시지 기록
        st.session_state.chat_history.append({
            "role": "ai",
            "content": answer
        })

        # input 값 초기화 (Streamlit 충돌 방지)
        st.session_state.ask_input = ""


# ==============================
# 대화 기록 UI
# ==============================
st.markdown("---")
st.subheader("대화 기록")

bubble_css = """
<style>
.user-bubble {
    background-color: #dce9f7;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
}
.ai-bubble {
    background-color: #fff5cc;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
}
</style>
"""
st.markdown(bubble_css, unsafe_allow_html=True)

for turn in st.session_state.chat_history:
    role = turn["role"]
    content = turn["content"]

    if role == "user":
        st.markdown(f"<div class='user-bubble'><b>사용자:</b><br>{content}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'><b>AI:</b><br>{content}</div>", unsafe_allow_html=True)

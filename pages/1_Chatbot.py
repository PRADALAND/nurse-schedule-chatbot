import streamlit as st
from utils.free_ai import call_llm

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

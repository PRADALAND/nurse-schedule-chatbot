import streamlit as st
from free_ai import call_llm

st.set_page_config(page_title="근무 스케줄 챗봇", layout="wide")

# CSS
st.markdown("""
<style>
.user-bubble {
    background-color: #dce9f7;
    color: #000000 !important;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
    max-width: 70%;
}
.ai-bubble {
    background-color: #f8f1c8;
    color: #000000 !important;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 20px;
    max-width: 70%;
}
</style>
""", unsafe_allow_html=True)

st.title("근무 스케줄 챗봇 (AI 기반)")

# 대화 저장 구조: dict 형태
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

query = st.text_input("질문을 입력하세요:")

if st.button("질문 보내기") and query:
    st.session_state.chat_history.append({"role": "user", "content": query})
    answer = call_llm(query)
    st.session_state.chat_history.append({"role": "ai", "content": answer})

st.subheader("대화 기록")

for turn in st.session_state.chat_history:
    if turn["role"] == "user":
        st.markdown(f"<div class='user-bubble'><b>사용자:</b><br>{turn['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'><b>AI:</b><br>{turn['content']}</div>", unsafe_allow_html=True)

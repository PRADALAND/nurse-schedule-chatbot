import streamlit as st
from utils.free_ai import call_llm

st.set_page_config(page_title="근무 스케줄 챗봇", layout="wide")

st.title("근무 스케줄 챗봇 (AI 기반)")
st.write("간호사 근무표와 근무 스케줄에 대해 질문하면, 근무 패턴 기반으로 분석을 도와드립니다.")

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# UI 스타일 (말풍선)
CHAT_CSS = """
<style>
.user-bubble {
    background-color: #dce8f8;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
    width: fit-content;
    max-width: 70%;
}
.ai-bubble {
    background-color: #f7efc7;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
    width: fit-content;
    max-width: 70%;
}
</style>
"""
st.markdown(CHAT_CSS, unsafe_allow_html=True)

# 입력받기
query = st.text_input("질문을 입력하세요:")

if st.button("질문 보내기") and query.strip():
    st.session_state.chat_history.append({"role": "user", "content": query})

    ai_response = call_llm(query)
    st.session_state.chat_history.append({"role": "ai", "content": ai_response})


st.subheader("대화 기록")

# 기록 출력
for turn in st.session_state.chat_history:
    if turn["role"] == "user":
        st.markdown(f"<div class='user-bubble'><b>사용자:</b><br>{turn['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'><b>AI:</b><br>{turn['content']}</div>", unsafe_allow_html=True)

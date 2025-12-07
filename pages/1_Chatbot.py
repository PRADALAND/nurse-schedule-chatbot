import streamlit as st
from utils.free_ai import call_llm

st.set_page_config(page_title="근무 스케줄 챗봇", layout="wide")

# CSS
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

# 세션 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("근무 스케줄 챗봇 (AI 기반)")

# -------------------------------
# 입력창
# -------------------------------
query = st.text_input("질문을 입력하세요.", key="ask_input")

# 제출 버튼
if st.button("질문 보내기"):
    if query.strip():

        # 기록
        st.session_state.chat_history.append(
            {"role": "user", "content": query.strip()}
        )

        answer = call_llm(query.strip())

        st.session_state.chat_history.append(
            {"role": "ai", "content": answer}
        )

        # 입력창 초기화 + rerun
        st.session_state.pop("ask_input", None)
        st.rerun()


# -------------------------------
# 대화 출력
# -------------------------------
st.markdown("---")
st.subheader("대화 기록")

for turn in st.session_state.chat_history:
    if turn["role"] == "user":
        st.markdown(
            f"<div class='user-bubble'><b>사용자:</b><br>{turn['content']}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='ai-bubble'><b>AI:</b><br>{turn['content']}</div>",
            unsafe_allow_html=True
        )

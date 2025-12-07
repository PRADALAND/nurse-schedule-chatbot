# pages/1_Chatbot.py

import streamlit as st
from utils.free_ai import call_llm  # 폴더 구조에 맞춘 import

st.set_page_config(page_title="근무 스케줄 챗봇", layout="wide")

# --------------------------------------------------
# 세션 상태 초기화: 항상 dict 리스트로 강제
# --------------------------------------------------
def init_chat_history():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        return

    # 기존에 tuple 등이 섞여 있으면 전부 버리고 새로 시작 (TypeError 방지)
    hist = st.session_state.chat_history
    if not isinstance(hist, list) or any(not isinstance(x, dict) for x in hist):
        st.session_state.chat_history = []

init_chat_history()

# --------------------------------------------------
# UI
# --------------------------------------------------
st.title("근무 스케줄 챗봇 (AI 기반)")
st.caption("근무표 데이터에 기반해 패턴·피로 위험·공정성 이슈를 질의응답 형식으로 분석합니다.")

user_input = st.text_input("궁금한 점을 질문해 주세요.", key="user_query")

col1, col2 = st.columns([1, 4])
with col1:
    send_clicked = st.button("질문 보내기")

# --------------------------------------------------
# 질문 처리
# --------------------------------------------------
if send_clicked and user_input.strip():
    # 사용자 질문 저장
    st.session_state.chat_history.append(
        {"role": "user", "content": user_input.strip()}
    )

    # LLM 호출
    answer = call_llm(user_input.strip())

    # AI 응답 저장
    st.session_state.chat_history.append(
        {"role": "ai", "content": answer}
    )

    # 입력창 비우기
    st.session_state.user_query = ""

# --------------------------------------------------
# 대화 기록 표시 (버블 스타일)
# --------------------------------------------------
st.markdown("---")
st.subheader("대화 기록")

chat_css = """
<style>
.chat-bubble {
  padding: 12px 14px;
  border-radius: 12px;
  margin-bottom: 8px;
  max-width: 80%;
}
.user-bubble {
  background-color: #dce9f7;
  margin-left: auto;
}
.ai-bubble {
  background-color: #f8f3c8;
  margin-right: auto;
}
.chat-role {
  font-weight: 700;
  margin-bottom: 4px;
}
</style>
"""
st.markdown(chat_css, unsafe_allow_html=True)

for turn in st.session_state.chat_history:
    role = turn.get("role", "ai")
    text = turn.get("content", "")

    if role == "user":
        bubble_class = "user-bubble"
        role_label = "사용자"
    else:
        bubble_class = "ai-bubble"
        role_label = "AI"

    st.markdown(
        f"""
        <div class="chat-bubble {bubble_class}">
          <div class="chat-role">{role_label}</div>
          <div>{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

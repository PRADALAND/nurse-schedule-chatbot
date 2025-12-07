import streamlit as st
from utils.free_ai import call_llm


# ==============================
# 페이지 기본 설정
# ==============================
st.set_page_config(page_title="근무 스케줄 챗봇", layout="wide")


# ==============================
# CSS 스타일링
# ==============================
bubble_css = """
<style>

.user-bubble {
    background-color: #dce9f7;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
    color: #000000 !important;
    border: 1px solid #b9d3ea;
}

.ai-bubble {
    background-color: #fff5cc;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
    color: #000000 !important;
    border: 1px solid #e6dca8;
}

</style>
"""
st.markdown(bubble_css, unsafe_allow_html=True)


# ==============================
# 세션 초기화
# ==============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ==============================
# UI: 입력창
# ==============================
st.title("근무 스케줄 챗봇 (AI 기반)")

query = st.text_input(
    "질문을 입력하세요.",
    key="ask_input",
    placeholder="예: 이번 달 최악의 근무 가진 간호사는 누구?"
)


# ==============================
# 버튼 처리
# ==============================
if st.button("질문 보내기"):    
    user_msg = query.strip()

    if user_msg:

        # 사용자 메시지 기록
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_msg
        })

        # LLM 호출
        answer = call_llm(user_msg)

        # AI 메시지 기록
        st.session_state.chat_history.append({
            "role": "ai",
            "content": answer
        })

        # **입력창 초기화 (Streamlit에서 가능한 유일한 안전한 방식)**
        st.session_state.pop("ask_input", None)
        st.rerun()


# ==============================
# UI: 대화 출력
# ==============================
st.markdown("---")
st.subheader("대화 기록")


for turn in st.session_state.chat_history:
    role = turn["role"]
    content = turn["content"]

    if role == "user":
        st.markdown(
            f"""
            <div class="user-bubble">
                <b>사용자:</b><br>
                {content}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="ai-bubble">
                <b>AI:</b><br>
                <span style="color:#000000;">{content}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

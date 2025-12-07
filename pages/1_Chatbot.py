import streamlit as st
from utils.free_ai import call_llm

# =========================================================
# 1) 페이지 설정 + 다크 모드 강제 방지
# =========================================================
st.set_page_config(page_title="근무 스케줄 챗봇", layout="wide")

# 전체 배경/글자색 강제 (다크모드에서 하얀 글자 문제 해결)
st.markdown("""
<style>
body, .stApp {
    background-color: white !important;
    color: black !important;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# 2) 말풍선 CSS (하얀색 문제 해결된 강제버전)
# =========================================================
bubble_css = """
<style>

.user-bubble {
    background-color: #dce9f7 !important;
    color: #000000 !important;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
    border: 1px solid #b9d3ea;
    display: block !important;
}

.ai-bubble {
    background-color: #fff5cc !important;
    color: #000000 !important;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
    border: 1px solid #e6dca8;
    display: block !important;
}

</style>
"""
st.markdown(bubble_css, unsafe_allow_html=True)


# =========================================================
# 3) 세션 초기화
# =========================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# =========================================================
# 4) 입력 UI
# =========================================================
st.title("근무 스케줄 챗봇 (AI 기반)")

query = st.text_input("질문을 입력하세요.", key="ask_input")


# =========================================================
# 5) 버튼 클릭 처리
# =========================================================
if st.button("질문 보내기"):
    if query.strip():

        # 사용자 기록
        st.session_state.chat_history.append({
            "role": "user",
            "content": query.strip()
        })

        # 모델 호출
        answer = call_llm(query.strip())

        # AI 기록
        st.session_state.chat_history.append({
            "role": "ai",
            "content": answer
        })

        # 입력창 초기화 + rerun
        st.session_state.pop("ask_input", None)
        st.rerun()


# =========================================================
# 6) 대화 표시
# =========================================================
st.markdown("---")
st.subheader("대화 기록")

for turn in st.session_state.chat_history:
    role = turn["role"]
    content = turn["content"]

    if role == "user":
        st.markdown(
            f"<div class='user-bubble'><b>사용자:</b><br>{content}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='ai-bubble'><b>AI:</b><br>{content}</div>",
            unsafe_allow_html=True
        )

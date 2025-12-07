import streamlit as st
from free_ai import ask_hf

# ============================================================
# UI 스타일 (가독성 + 색상 문제 해결)
# ============================================================

USER_BG = "#dce9f7"     # 연한 하늘색
AI_BG   = "#f7f0c8"     # 연한 크림색
TEXT_COLOR = "#111111"  # 모든 텍스트 짙은 색으로 고정

st.set_page_config(page_title="근무 스케줄 챗봇", layout="wide")

# CSS
st.markdown(
    f"""
    <style>
        body, .stTextInput, .stButton, .stMarkdown {{
            color: {TEXT_COLOR} !important;
        }}
        .user-msg {{
            background-color: {USER_BG};
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 8px;
        }}
        .ai-msg {{
            background-color: {AI_BG};
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 16px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# Streamlit 앱
# ============================================================

st.title("근무 스케줄 챗봇 (AI 기반)")
st.write("간호사 근무표와 스케줄 관련 질문을 입력하면, 근거 기반 분석을 제공합니다.")

# 대화 기록 저장
if "messages" not in st.session_state:
    st.session_state.messages = []

question = st.text_input("질문을 입력하세요:")

if st.button("질문 보내기") and question:
    st.session_state.messages.append(("user", question))

    answer = ask_hf(question)
    st.session_state.messages.append(("ai", answer))

# 대화 히스토리 렌더링
st.subheader("대화 기록")
for role, msg in st.session_state.messages:
    if role == "user":
        st.markdown(f"<div class='user-msg'><b>사용자:</b><br>{msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-msg'><b>AI:</b><br>{msg}</div>", unsafe_allow_html=True)

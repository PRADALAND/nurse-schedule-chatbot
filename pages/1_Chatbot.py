import streamlit as st
from utils.free_ai import call_llm

st.set_page_config(page_title="근무 스케줄 챗봇", layout="wide")

# ==============================
# 세션 초기화
# ==============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 잘못된 항목 정리
cleaned = []
for item in st.session_state.chat_history:
    if isinstance(item, dict) and "role" in item and "content" in item:
        cleaned.append(item)
st.session_state.chat_history = cleaned

# ==============================
# 입력 UI
# ==============================
st.title("근무 스케줄 챗봇 (AI 기반)")

query = st.text_input(
    "질문을 입력하세요.",
    key="ask_input"
)

if st.button("질문 보내기"):
    if query.strip():

        # 대화 기록 저장
        st.session_state.chat_history.append({
            "role": "user",
            "content": query.strip()
        })

        answer = call_llm(query.strip())

        st.session_state.chat_history.append({
            "role": "ai",
            "content": answer
        })

        # 입력 리셋
        st.session_state.pop("ask_input", None)
        st.rerun()

# ==============================
# 대화 출력
# ==============================
st.markdown("---")
st.subheader("대화 기록")

for turn in st.session_state.chat_history:
    role = turn["role"]
    content = turn["content"]

    if role == "user":
        st.markdown(f"<div style='background:#dce9f7;padding:12px;border-radius:10px;margin-bottom:8px'><b>사용자:</b><br>{content}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background:#fff5cc;padding:12px;border-radius:10px;margin-bottom:8px'><b>AI:</b><br>{content}</div>", unsafe_allow_html=True)

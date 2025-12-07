import streamlit as st
from utils.free_ai import call_llm

# ==============================
# 스타일 요소
# ==============================
bubble_css = """
<style>
.chat-container { margin-top: 10px; }

.user-bubble {
    background-color: #dce9f7;
    color: #000000 !important;
    padding: 12px 14px;
    border-radius: 12px;
    margin-bottom: 10px;
    font-size: 16px;
    line-height: 1.5;
    border: 1px solid #b9d3ea;
}

.ai-bubble {
    background-color: #fff5cc;
    color: #000000 !important;
    padding: 12px 14px;
    border-radius: 12px;
    margin-bottom: 10px;
    font-size: 16px;
    line-height: 1.5;
    border: 1px solid #e6dca8;
}

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

# 잘못된 값 제거
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
    key="ask_input",
    placeholder="예: 다음 주 근무 일정 알려줘"
)

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

        # 입력 초기화 방법 (위젯 직접 수정 금지 → rerun 사용)
        st.session_state.ask_input = ""  # 안전함: rerun 직전에만 변경
        st.rerun()  # rerun으로 입력창은 빈 문자열로 초기화됨


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

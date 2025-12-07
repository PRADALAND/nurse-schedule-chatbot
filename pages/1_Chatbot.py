query = st.text_input(
    "질문을 입력하세요.",
    key="ask_input"
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

        # 입력창 초기화 (Streamlit 공식적으로 허용되는 방식)
        st.session_state.pop("ask_input", None)
        st.rerun()

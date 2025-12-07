import streamlit as st

st.set_page_config(page_title="AI 분석 기록 대시보드", layout="wide")

st.title("AI 분석 기록 대시보드")

# 세션 스테이트에서 로그 읽기
logs = st.session_state.get("analysis_logs", [])

if not logs:
    st.info("현재까지 저장된 AI 분석 로그가 없습니다.")
    st.stop()

st.markdown("### 저장된 분석 기록")

for item in logs:
    st.markdown(
        f"""
        **시간:** {item['timestamp']}  
        **질문:** {item['query']}  
        **응답:** {item['response']}  
        ---
        """
    )

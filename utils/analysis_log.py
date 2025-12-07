import datetime
import streamlit as st


def log_analysis(user_query, response):
    """사용자 질의와 응답을 session_state에 저장."""
    if "analysis_logs" not in st.session_state:
        st.session_state["analysis_logs"] = []

    st.session_state["analysis_logs"].append(
        {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": user_query,
            "response": response,
        }
    )


def fetch_logs():
    """저장된 로그 반환."""
    return st.session_state.get("analysis_logs", [])

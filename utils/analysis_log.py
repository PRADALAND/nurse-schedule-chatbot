import datetime
import streamlit as st
import pandas as pd


def log_analysis(user_query, response):
    """챗봇 분석 로그 기록"""
    if "analysis_logs" not in st.session_state:
        st.session_state["analysis_logs"] = []

    st.session_state["analysis_logs"].append({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": user_query,
        "response": response,
    })


def fetch_logs():
    """로그 대시보드에서 로그를 불러오는 함수"""
    logs = st.session_state.get("analysis_logs", [])
    if not logs:
        return pd.DataFrame(columns=["timestamp", "query", "response"])
    return pd.DataFrame(logs)

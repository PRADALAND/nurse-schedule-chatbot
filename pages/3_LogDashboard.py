import streamlit as st
import pandas as pd

st.title("AI 분석 기록 대시보드")

logs = st.session_state.get("analysis_logs", [])

if not logs:
    st.info("아직 분석 로그가 없습니다.")
    st.stop()

df = pd.DataFrame(logs)
st.dataframe(df)

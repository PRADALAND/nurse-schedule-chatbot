import streamlit as st
import pandas as pd
from utils.analysis_log import fetch_logs

def main():
    st.title("AI 분석 기록 대시보드")

    df = fetch_logs()

    if df.empty:
        st.info("아직 기록된 분석 로그가 없습니다.")
        return

    st.subheader("전체 로그")
    st.dataframe(df)

    # 최근 로그 강조
    st.subheader("최근 5개 로그")
    st.table(df.tail(5))

if __name__ == "__main__":
    main()

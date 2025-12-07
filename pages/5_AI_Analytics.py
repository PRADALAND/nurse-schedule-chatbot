import streamlit as st
from utils.analysis_log import fetch_logs

st.title("AI 분석 기록 대시보드")

logs = fetch_logs()

if not logs:
    st.info("아직 기록된 분석 로그가 없습니다.")
    st.stop()

# 표로 표시하기 위해 데이터프레임 변환
import pandas as pd
df_logs = pd.DataFrame(logs)

st.subheader("AI 응답 로그 (최신순)")
st.dataframe(df_logs[::-1], use_container_width=True)

# 각 로그 상세 보기
st.subheader("상세 로그 열람")

for i, row in enumerate(df_logs[::-1].to_dict("records"), start=1):
    with st.expander(f"[{row['timestamp']}] 질의 내용 보기"):
        st.write("질문:")
        st.code(row["query"])
        st.write("응답:")
        st.write(row["response"])

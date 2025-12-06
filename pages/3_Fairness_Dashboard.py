import streamlit as st
import pandas as pd
from utils.fairness import compute_fairness_table

def main():
    st.title("공정성 대시보드")

    df = st.session_state.get("schedule_df")

    # 1) 파일이 안 올라온 경우
    if df is None:
        st.warning("스케줄 파일을 먼저 업로드해주세요.")
        return

    # 2) df 개요 표시 (디버깅용)
    st.subheader("DEBUG: 원본 데이터 구조")
    st.write(df.head())
    st.write(df.columns.tolist())

    # 3) 공정성 테이블 생성
    try:
        fair = compute_fairness_table(df)
    except Exception as e:
        st.error(f"compute_fairness_table 오류: {e}")
        return

    # 4) 공정성 테이블 출력
    st.subheader("공정성 요약 테이블")
    st.dataframe(fair)

    if fair.empty:
        st.warning("공정성 데이터가 비어 있습니다.")
        return

    # 5) RN 선택
    selected = st.selectbox("간호사 선택", fair["nurse_name"])
    row = fair[fair["nurse_name"] == selected].iloc[0]

    st.subheader("개별 간호사 분석")
    st.write(row)

if __name__ == "__main__":
    main()

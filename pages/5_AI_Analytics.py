# pages/5_AI_Analytics.py

import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
from utils.analysis_log import fetch_logs

def main():
    st.title("AI 분석 기록 대시보드")

    logs = fetch_logs(limit=200)
    if not logs:
        st.info("아직 분석 기록이 없습니다.")
        return

    df = pd.DataFrame(logs)

    st.subheader("🗂 전체 분석 로그 테이블")
    st.dataframe(df[["created_at", "user_id", "file_name", "file_type", "user_prompt"]])

    st.markdown("---")

    st.subheader("🔍 개별 로그 상세 보기")

    idx = st.selectbox("조회할 로그 선택", range(len(df)))
    row = df.iloc[idx]

    st.write(f"**시간:** {row['created_at']}")
    st.write(f"**사용자:** {row['user_id']}")
    st.write(f"**파일 이름:** {row['file_name']}")
    st.write(f"**파일 타입:** {row['file_type']}")
    st.write(f"**요청 내용:** {row['user_prompt']}")

    st.markdown("### 🤖 AI 분석 결과")
    st.write(row["ai_summary"])

    # 파일 타입 따라 미리보기
    if row["file_type"] == "csv":
        st.markdown("### 📊 CSV 미리보기 (상위 20행)")
        csv_bytes = requests.get(row["file_url"]).content
        csv_df = pd.read_csv(BytesIO(csv_bytes))
        st.dataframe(csv_df.head(20))

    elif row["file_type"] == "image":
        img_bytes = requests.get(row["file_url"]).content
        img = Image.open(BytesIO(img_bytes))
        st.markdown("### 🖼 이미지 미리보기")
        st.image(img)

    st.markdown("---")

    # 메타 분석 (전체 로그 기반 통계)
    st.subheader("📈 AI 메타분석 (요약)")
    st.write(f"- 총 업로드된 파일 수: **{len(df)}개**")
    st.write(f"- CSV 파일 수: **{(df['file_type']=='csv').sum()}개**")
    st.write(f"- 이미지 파일 수: **{(df['file_type']=='image').sum()}개**")

if __name__ == "__main__":
    main()

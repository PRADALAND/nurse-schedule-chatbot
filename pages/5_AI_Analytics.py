import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
from utils.analysis_log import fetch_logs

def main():
    st.title("AI Analytics Dashboard")

    logs = fetch_logs(limit=200)
    if not logs:
        st.info("분석 데이터 없음")
        return

    df = pd.DataFrame(logs)
    st.dataframe(df[["created_at", "file_name", "file_type", "user_prompt"]])

    idx = st.selectbox("상세보기", range(len(df)))
    row = df.iloc[idx]

    st.subheader("AI Summary")
    st.write(row["ai_summary"])

    if row["file_type"] == "csv":
        csv_bytes = requests.get(row["file_url"]).content
        csv_df = pd.read_csv(BytesIO(csv_bytes))
        st.subheader("CSV Preview")
        st.dataframe(csv_df.head(30))

    if row["file_type"] == "image":
        img_bytes = requests.get(row["file_url"]).content
        img = Image.open(BytesIO(img_bytes))
        st.subheader("Image Preview")
        st.image(img)

if __name__ == "__main__":
    main()


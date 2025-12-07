import streamlit as st
import pandas as pd
import requests
import os
import json

# =========================================================
# HF Router API 설정
# =========================================================
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"


# =========================================================
# LLM 호출 함수
# =========================================================
def call_llm(system_prompt: str, user_prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.2,
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload)

        if resp.status_code != 200:
            return f"❌ API 오류 {resp.status_code}: {resp.text}"

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"❌ 호출 오류: {e}"


# =========================================================
# 근무 스케줄 분석 알고리즘
# =========================================================
def compute_workload_score(df):
    # 점수 매핑
    score_map = {
        "N": 3, "NS": 3, "NIGHT": 3,
        "E": 2, "EVENING": 2,
        "D": 1, "DAY": 1, "9D": 1, "8D": 1, "DS": 1,
        "OFF": 0, "O": 0, "휴무": 0
    }

    df["shift_norm"] = df["shift_code"].str.upper().str.strip()
    df["score"] = df["shift_norm"].map(score_map).fillna(0)

    # 연속 야간 근무 패널티
    df = df.sort_values(["nurse_id", "date"])
    df["night_streak"] = (df["shift_norm"].isin(["N", "NS", "NIGHT"])).astype(int)
    df["penalty"] = 0

    for nurse in df["nurse_id"].unique():
        nurse_data = df[df["nurse_id"] == nurse]
        streak = 0
        penalties = []
        for shift in nurse_data["night_streak"]:
            if shift == 1:
                streak += 1
            else:
                streak = 0
            penalties.append(max(0, streak - 1))  # 연속 2번째부터 패널티
        df.loc[nurse_data.index, "penalty"] = penalties

    df["total_score"] = df["score"] + df["penalty"]

    return df


def summarize_scores(df):
    summary = df.groupby(["nurse_id", "nurse_name"])["total_score"].sum().reset_index()
    summary = summary.sort_values("total_score", ascending=False)
    worst = summary.iloc[0]

    return summary, worst


# =========================================================
# Streamlit UI
# =========================================================
def main():
    st.title("근무 스케줄 챗봇 (AI 기반)")

    uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])

    # CSV를 session_state에 저장하여 유지
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.session_state["df"] = df
        st.write("업로드된 스케줄 미리보기:", df.head())

    query = st.text_input("질문을 입력하세요.")

    if st.button("질문 보내기") and query.strip():

        # CSV 없으면 오류
        if "df" not in st.session_state:
            st.error("먼저 CSV 파일을 업로드하세요!")
            return

        df = st.session_state["df"]

        # Python 분석 수행
        df_scored = compute_workload_score(df)
        summary, worst = summarize_scores(df_scored)

        # LLM에게 넘기는 데이터 (요약만 전달)
        analysis_text = (
            "전체 근무 부담 점수 요약:\n"
            + summary.to_string(index=False)
            + "\n\n"
            + f"최악의 근무자는 {worst['nurse_name']} (총점 {worst['total_score']}) 입니다.\n"
        )

        system_prompt = (
            "너는 간호사 근무 스케줄 분석 전문가다. "
            "반드시 내가 제공한 분석 결과만 기반으로 답변해야 하며, "
            "추가 추론이나 임의 가정은 절대 금지다."
        )

        user_prompt = f"사용자 질문: {query}\n\n분석 결과:\n{analysis_text}"

        answer = call_llm(system_prompt, user_prompt)

        st.subheader("AI 응답")
        st.markdown(answer)

        st.subheader("백엔드 분석 결과")
        st.text(analysis_text)


if __name__ == "__main__":
    main()

# utils/free_ai.py

import os
import base64
import pandas as pd
import streamlit as st
from huggingface_hub import InferenceClient

# -------------------------------------------------------
# 1) HuggingFace API KEY 로드
# -------------------------------------------------------
HF_API_KEY = os.getenv("HF_API_KEY") or st.secrets.get("HF_API_KEY")

if HF_API_KEY is None:
    raise ValueError(
        "HF_API_KEY가 설정되어 있지 않습니다. "
        "Streamlit secrets.toml 또는 환경변수에 HF_API_KEY를 추가하세요."
    )

# -------------------------------------------------------
# 2) 무료 텍스트 LLM (text-generation 지원되는 모델만!)
# -------------------------------------------------------
LLM = InferenceClient(
    "mistralai/Mistral-7B-Instruct-v0.2",
    token=HF_API_KEY,
)

# -------------------------------------------------------
# 3) 무료 이미지 캡션 모델
# -------------------------------------------------------
VISION = InferenceClient(
    "nlpconnect/vit-gpt2-image-captioning",
    token=HF_API_KEY,
)


# -------------------------------------------------------
# 4) CSV 분석 함수
# -------------------------------------------------------
def analyze_csv_free(df: pd.DataFrame, prompt: str) -> str:
    sample = df.head(20).to_string()
    full_prompt = (
        "You are a data analyst. Analyze the CSV and answer the user's question.\n"
        f"User question: {prompt}\n\n"
        f"CSV Preview:\n{sample}"
    )

    resp = LLM.text_generation(
        full_prompt,
        max_new_tokens=300,
        temperature=0.2,
    )

    # resp는 dict 구조이므로 ['generated_text'] 기본 접근
    if isinstance(resp, dict) and "generated_text" in resp:
        return resp["generated_text"]

    return str(resp)


# -------------------------------------------------------
# 5) 이미지 분석 함수
# -------------------------------------------------------
def analyze_image_free(image_bytes: bytes, prompt: str) -> str:
    # 이미지 Base64 인코딩
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    resp = VISION.image_to_text(
        {"inputs": b64},
        max_new_tokens=80,
    )

    caption = resp.get("generated_text", "(no caption)")
    return f"Image caption: {caption}\nUser question: {prompt}"

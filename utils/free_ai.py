# utils/free_ai.py

import os
import base64
import pandas as pd
import streamlit as st
from huggingface_hub import InferenceClient

# =========================================
# API Key 로드
# =========================================
HF_API_KEY = os.getenv("HF_API_KEY") or st.secrets.get("HF_API_KEY")

if HF_API_KEY is None:
    raise ValueError(
        "HF_API_KEY가 설정되어 있지 않습니다. "
        "Streamlit secrets.toml 또는 환경변수에 HF_API_KEY를 추가하세요."
    )

# =========================================
# 무료 LLM (CSV 분석용)
# =========================================
LLM = InferenceClient(
    "mistralai/Mistral-7B-Instruct-v0.2",
    token=HF_API_KEY,
)

# =========================================
# 무료 이미지 캡션 모델
# =========================================
VISION = InferenceClient(
    "nlpconnect/vit-gpt2-image-captioning",
    token=HF_API_KEY,
)


# =========================================
# CSV 분석 함수
# =========================================
def analyze_csv_free(df: pd.DataFrame, prompt: str) -> str:
    """
    CSV 파일 일부를 기반으로 무료 LLM 분석.
    """
    sample = df.head(20).to_csv(index=False)
    full_prompt = (
        "You are an expert clinical data analyst for nurse scheduling.\n"
        "Given the CSV preview below, analyze workload, night shifts, quick returns, "
        "and fatigue/safety patterns. Answer in Korean.\n\n"
        f"사용자 요청:\n{prompt}\n\n"
        f"CSV Preview:\n{sample}"
    )

    response = LLM.text_generation(
        full_prompt,
        max_new_tokens=350,
        temperature=0.2,
    )

    return response


# =========================================
# 이미지 분석 함수
# =========================================
def analyze_image_free(image_bytes: bytes, prompt: str) -> str:
    """
    무료 이미지 캡션 모델 기반 분석
    """
    result = VISION.image_to_text(image=image_bytes)

    # HuggingFace API가 반환하는 다양한 포맷 방어 처리
    if isinstance(result, str):
        caption = result
    elif isinstance(result, dict) and "generated_text" in result:
        caption = result["generated_text"]
    elif isinstance(result, list) and len(result) > 0:
        first = result[0]
        if isinstance(first, dict) and "generated_text" in first:
            caption = first["generated_text"]
        else:
            caption = str(first)
    else:
        caption = str(result)

    final_text = (
        "이미지 자동 캡션 결과:\n"
        f"- {caption}\n\n"
        "추가 해석:\n"
        f"- 사용자 요청 '{prompt}'에 따라, 이미지에서 확인 가능한 구조·패턴 정보를 "
        "기반으로 개괄적 상황 판단에 활용할 수 있습니다."
    )

    return final_text

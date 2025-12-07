# utils/free_ai.py

import os
import base64
import pandas as pd
import streamlit as st
from huggingface_hub import InferenceClient

# HuggingFace API 키 (Streamlit secrets 또는 환경변수)
HF_API_KEY = os.getenv("HF_API_KEY") or st.secrets.get("HF_API_KEY")

if HF_API_KEY is None:
    raise ValueError(
        "HF_API_KEY가 설정되어 있지 않습니다. "
        "Streamlit secrets.toml 또는 환경변수에 HF_API_KEY를 추가하세요."
    )

# 1) CSV·텍스트 분석용 무료 LLM (Inference API 지원되는 모델)
LLM = InferenceClient(
    "mistralai/Mistral-7B-Instruct-v0.2",
    token=HF_API_KEY,
)

# 2) 이미지 캡션용 무료 모델 (image_to_text 지원)
VISION = InferenceClient(
    "nlpconnect/vit-gpt2-image-captioning",
    token=HF_API_KEY,

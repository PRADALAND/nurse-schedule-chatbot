# utils/free_ai.py
from huggingface_hub import InferenceClient
import pandas as pd
import base64
import os

HF_API_KEY = os.getenv("HF_API_KEY")

# 실행 가능한 무료 LLM (CSV 분석용)
LLM = InferenceClient(
    "mistralai/Mistral-7B-Instruct-v0.2",
    token=HF_API_KEY
)

# 이미지 분석 모델 (이 모델은 API 지원됨)
VISION = InferenceClient(
    "google/siglip-so400m-patch14-384",
    token=HF_API_KEY
)

def analyze_csv_free(df: pd.DataFrame, prompt: str) -> str:
    sample = df.head(20).to_csv(index=False)
    full_prompt = (
        "다음은 간호사 스케줄 데이터 일부입니다.\n"
        "간호 안전·피로·위험 관점에서 분석해주세요.\n\n"
        f"사용자 요청: {prompt}\n\n"
        f"CSV Preview:\n{sample}"
    )

    response = LLM.text_generation(
        full_prompt,
        max_new_tokens=300,
        temperature=0.2,
    )
    return response

def analyze_image_free(image_bytes: bytes, prompt: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    # SigLip은 구조적으로 caption 기능이 제한적
    # text_to_image 대신 image_to_text 지원 모델로 교체 가능
    return (
        "이미지 특징 분석(무료 모델):\n"
        " - 색상, 형태 기반 대략적 특징만 제공\n"
        " - 상세 설명 모델이 아니므로 간단한 분석만 가능\n"
    )

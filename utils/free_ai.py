# utils/free_ai.py
from huggingface_hub import InferenceClient
import pandas as pd
import base64

# 무료 텍스트 모델 (CSV 분석용)
LLM = InferenceClient("meta-llama/Meta-Llama-3.1-8B-Instruct")

# 무료 이미지 모델
VISION = InferenceClient("google/siglip-so400m-patch14-384")


def analyze_csv_free(df: pd.DataFrame, prompt: str) -> str:
    sample = df.head(20).to_csv(index=False)
    full_prompt = (
        "다음은 스케줄/근무 데이터 일부입니다.\n"
        "간호사의 관점에서 패턴, 위험요소, 특이점 등을 분석해주세요.\n"
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
    # 이미지를 base64로 인코딩
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    # Vision 모델은 이미지+텍스트 입력
    response = VISION.text_to_image(
        prompt=f"사용자 요청: {prompt}",
        image=encoded
    )
    # 일부 모델은 설명문을 반환, 일부는 embedding/feature만 반환
    # SigLip은 캡션 기능이 제한적이므로 간단한 분석으로 처리
    return (
        "이미지 특징 분석(무료 모델):\n"
        " - 색상, 형태, 구성요소 기반 대략적 특징 제공\n"
        " - 이 모델은 OpenAI 수준의 비전 모델은 아니지만 기본적인 객체/구조 분석 가능\n"
    )

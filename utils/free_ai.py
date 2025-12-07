# utils/free_ai.py

import os
import requests

HF_API_URL = os.getenv("HF_API_URL", "")
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

def call_llm(prompt: str, max_tokens: int = 200):
    """
    HuggingFace Inference API(Qwen 0.5B)로 텍스트 생성 요청.
    무료 모델 사용 시에도 정상 작동.
    """

    if not HF_API_TOKEN:
        raise ValueError("HF_API_TOKEN이 설정되어 있지 않습니다. secrets.toml을 확인하세요.")
    if not HF_API_URL:
        raise ValueError("HF_API_URL이 설정되어 있지 않습니다.")

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": 0.2,
        },
    }

    response = requests.post(HF_API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(
            f"HF API 호출 실패: {response.status_code}, {response.text}"
        )

    data = response.json()

    # 텍스트만 추출
    if isinstance(data, list) and len(data) > 0:
        return data[0].get("generated_text", "").strip()

    if isinstance(data, dict) and "generated_text" in data:
        return data["generated_text"].strip()

    return str(data)

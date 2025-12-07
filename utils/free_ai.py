# utils/free_ai.py

import os
import requests

# -----------------------------------------------------
# 환경변수 설정
# -----------------------------------------------------

HF_TOKEN = os.getenv("HF_API_TOKEN") or os.getenv("HF_TOKEN")

# 반드시 /v1/responses 이어야 정상 작동
HF_URL = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/responses")

# 네가 요청한 모델
HF_MODEL = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")


class HFConfigError(RuntimeError):
    pass


def _ensure_config():
    """필수 환경변수 확인."""
    if not HF_TOKEN:
        raise HFConfigError(
            "HF_API_TOKEN 또는 HF_TOKEN 환경변수가 없습니다."
        )
    if not HF_URL.startswith("http"):
        raise HFConfigError(f"HF_API_URL이 잘못되었습니다: {HF_URL!r}")
    if not HF_MODEL:
        raise HFConfigError("HF_MODEL 환경변수가 비어 있습니다.")


def call_llm(user_prompt: str) -> str:
    """
    스트림릿 챗봇에서 호출하는 LLM 함수.
    입력: 한국어 프롬프트 string
    출력: 모델의 한국어 답변 string
    """
    _ensure_config()

    if not user_prompt or not user_prompt.strip():
        return "입력된 질문이 없습니다."

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    # 시스템 프롬프트 — 너의 스케줄링 챗봇에 맞게 최소한의 안전성만 부여
    system_prompt = (
        "You are an AI assistant in a Korean nurse scheduling analysis app. "
        "Answer concisely in Korean. "
        "Base your reply strictly on the prompt and precomputed statistics. "
        "Do NOT hallucinate unknown schedule data."
    )

    payload = {
        "model": HF_MODEL,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_output_tokens": 512,
        "temperature": 0.3,
    }

    try:
        response = requests.post(HF_URL, headers=headers, json=payload, timeout=40)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"HF API 네트워크 오류: {e}") from e

    if response.status_code != 200:
        # Streamlit에서 debugging 가능하도록 그대로 노출
        raise RuntimeError(
            f"HF API Error {response.status_code}: {response.text}"
        )

    data = response.json()

    # Responses API 응답 구조 파싱
    try:
        outputs = data.get("output", [])
        if outputs:
            first = outputs[0]
            contents = first.get("content", [])
            for c in contents:
                if c.get("type") in ("output_text", "text"):
                    text = c.get("text", "").strip()
                    if text:
                        return text

        # fallback — 혹시 output_text 라는 필드가 따로 있을 경우
        if "output_text" in data:
            text = data["output_text"]
            if isinstance(text, str) and text.strip():
                return text.strip()

    except Exception:
        # 파싱 문제 발생 시 원문 공급
        return str(data)

    # 아무것도 얻지 못했다면 전체 JSON 반환
    return str(data)

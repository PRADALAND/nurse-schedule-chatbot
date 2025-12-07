# utils/free_ai.py

import os
import requests

# ======================================================
# 환경변수 로딩
# ======================================================

HF_TOKEN = os.getenv("HF_API_TOKEN") or os.getenv("HF_TOKEN")
HF_URL = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/responses")
HF_MODEL = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")


class HFConfigError(RuntimeError):
    pass


def _ensure_config():
    """필수 환경변수 확인"""
    if not HF_TOKEN:
        raise HFConfigError("HF_API_TOKEN / HF_TOKEN 환경변수가 없습니다.")
    if not HF_URL.startswith("http"):
        raise HFConfigError(f"HF_API_URL 형식 오류: {HF_URL}")
    if not HF_MODEL:
        raise HFConfigError("HF_MODEL 환경변수가 비어 있습니다.")


# ======================================================
# LLM 호출 함수
# ======================================================
def call_llm(user_prompt: str) -> str:
    """
    병동 스케줄 분석용 LLM 호출 함수.
    - 반드시 한국어만 출력
    - chain-of-thought 절대 노출 금지
    - 데이터 부족해도 가능한 범위 최대 분석 수행
    """

    _ensure_config()

    if not user_prompt or not user_prompt.strip():
        return "입력된 질문이 없습니다."

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    # ================================================
    # 🔥 최적화된 SYSTEM PROMPT — 절대 고치지 않는 것을 추천
    # ================================================
    system_prompt = (
        "너는 한국 병동의 근무 스케줄을 분석하는 전문 AI이다. "
        "출력은 반드시 **한국어로만** 작성한다. "
        "내부 추론 과정, chain-of-thought, 사고 과정은 절대로 노출하지 않는다. "
        "사용자가 제공한 통계가 불완전하더라도, "
        "그 정보 안에서 **가능한 모든 상대적 분석·추정**을 제공해야 한다. "
        "단, 존재하지 않는 근무 데이터를 마음대로 만들면 안 된다. "
        "답변은 반드시 다음 3단 구조로 작성한다:\n"
        "1) 가능한 상대적 분석: 제공된 정보 안에서 최대한 의미 있는 해석을 제시\n"
        "2) 한계: 왜 정확한 판정이 어려운지, 어떤 정보가 부족한지\n"
        "3) 필요한 데이터: 더 정확한 분석을 위해 필요한 최소 데이터 2~3개\n"
        "이 세 가지는 항상 포함해야 한다."
    )

    # ================================================
    # 모델 입력 payload
    # ================================================
    payload = {
        "model": HF_MODEL,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_output_tokens": 600,
        "temperature": 0.25,   # 안정적 분석을 위해 낮게 유지
    }

    # ================================================
    # API 요청
    # ================================================
    try:
        response = requests.post(HF_URL, headers=headers, json=payload, timeout=40)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"HF API 네트워크 오류: {e}") from e

    if response.status_code != 200:
        raise RuntimeError(
            f"HF API Error {response.status_code}: {response.text}"
        )

    data = response.json()

    # ================================================
    # HuggingFace Responses API 파싱
    # ================================================
    try:
        outputs = data.get("output", [])
        if outputs:
            content_blocks = outputs[0].get("content", [])
            for c in content_blocks:
                if c.get("type") in ("output_text", "text"):
                    text = c.get("text", "").strip()
                    if text:
                        return text

        # fallback
        if isinstance(data.get("output_text"), str):
            return data["output_text"].strip()

    except Exception:
        return str(data)

    return str(data)

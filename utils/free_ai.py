# utils/free_ai.py

import os
import requests

# ----------------------------
# 환경변수 읽기
# ----------------------------
# 둘 중 아무거나 있으면 사용 (기존 HF_API_TOKEN 유지용)
HF_TOKEN = os.getenv("HF_API_TOKEN") or os.getenv("HF_TOKEN")

# Hugging Face Router Responses API 엔드포인트
# ⚠️ 지금 네 환경에 HF_API_URL="https://router.huggingface.co/inference" 로 들어가 있다면
#    반드시 지우거나 "https://router.huggingface.co/v1/responses" 로 바꿔야 한다.
HF_URL = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/responses")

# 기본 모델: 네가 말한 DeepSeek-R1-Distill-Qwen-1.5B
# (단, 이 모델은 Inference Providers에 없기 때문에, router에서 그대로는 안 돌아간다.)
HF_MODEL = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B")


class HFConfigError(RuntimeError):
    """환경설정(HF 토큰/URL/모델) 관련 오류용 예외."""
    pass


def _ensure_config():
    """필수 환경구성이 있는지 확인."""
    if not HF_TOKEN:
        raise HFConfigError(
            "HF_API_TOKEN 또는 HF_TOKEN 환경변수가 설정되어 있지 않습니다. "
            "Streamlit Cloud의 Secrets 또는 환경변수 설정에서 토큰을 넣어주세요."
        )
    if not HF_URL.startswith("http"):
        raise HFConfigError(
            f"HF_API_URL 값이 올바른 URL이 아닙니다: {HF_URL!r}"
        )
    if not HF_MODEL:
        raise HFConfigError(
            "HF_MODEL 환경변수가 비어 있습니다. "
            "예: HF_MODEL='deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B'"
        )


def call_llm(user_prompt: str) -> str:
    """
    nurse-schedule 챗봇에서 사용하는 LLM 호출 함수.
    입력: 한국어 프롬프트 문자열 1개
    출력: 모델이 생성한 한국어 응답 (string)
    """
    _ensure_config()

    if not user_prompt or not user_prompt.strip():
        return "질문이 비어 있습니다. 분석할 내용을 구체적으로 적어 주세요."

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    # 가능하면 환자/동료 이름 등은 추측하지 않고, 스케줄 통계에만 기반해 요약하도록 유도
    system_prompt = (
        "You are an AI assistant embedded in a Korean nurse schedule analysis app. "
        "You must answer briefly in Korean. "
        "Use only the information given in the question and the pre-computed statistics "
        "from the app. Do not make up any schedule data or personal information. "
        "If something is unknown, clearly say that you do not know."
    )

    payload = {
        "model": HF_MODEL,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # Responses API 옵션 (문서 기준)
        "max_output_tokens": 512,
        "temperature": 0.3,
    }

    try:
        resp = requests.post(HF_URL, headers=headers, json=payload, timeout=40)
    except requests.exceptions.RequestException as e:
        # 네가 Streamlit에서 그대로 볼 수 있도록 RuntimeError로 래핑
        raise RuntimeError(f"HF API 네트워크 오류: {e}") from e

    # HTTP 에러 처리
    if resp.status_code != 200:
        # DeepSeek 1.5B 같이 Provider 미지원 모델일 때 나오는 메시지를 그대로 보여줌
        raise RuntimeError(
            f"HF API Error {resp.status_code}: {resp.text}"
        )

    data = resp.json()

    # Responses API의 표준 응답 구조 파싱
    # 예시: 
    # {
    #   "id": "...",
    #   "output": [
    #     {
    #       "role": "assistant",
    #       "content": [
    #         {"type": "output_text", "text": "모델 응답..."}
    #       ]
    #     }
    #   ],
    #   ...
    # }
    try:
        outputs = data.get("output", [])
        if outputs:
            first = outputs[0]
            contents = first.get("content", [])
            for c in contents:
                if c.get("type") in ("output_text", "text"):
                    text = c.get("text", "")
                    if isinstance(text, str) and text.strip():
                        return text.strip()

        # 혹시 top-level에 output_text가 있는 경우 대비
        if "output_text" in data:
            text = data["output_text"]
            if isinstance(text, str) and text.strip():
                return text.strip()
    except Exception:
        # 파싱 실패 시 전체 JSON을 string으로 반환 (디버깅용)
        return str(data)

    # 여기까지 왔는데도 텍스트가 없으면, 원시 JSON을 보여 줘서 디버깅에 도움되게 함
    return str(data)

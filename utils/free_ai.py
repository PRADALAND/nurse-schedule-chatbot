# utils/free_ai.py

import os
import requests


# -----------------------------------------------------
# 1) 환경변수 로딩
# -----------------------------------------------------

HF_TOKEN = os.getenv("HF_API_TOKEN") or os.getenv("HF_TOKEN")
HF_URL = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/responses")
HF_MODEL = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")


# -----------------------------------------------------
# 2) 오류 유형 정의
# -----------------------------------------------------

class HFConfigError(RuntimeError):
    """환경변수 오류."""
    pass


# -----------------------------------------------------
# 3) 환경변수 유효성 검사
# -----------------------------------------------------

def _ensure_config():
    if not HF_TOKEN:
        raise HFConfigError("HF_API_TOKEN 또는 HF_TOKEN 환경변수가 없습니다.")
    if not HF_URL.startswith("http"):
        raise HFConfigError(f"HF_API_URL이 잘못되었습니다: {HF_URL!r}")
    if not HF_MODEL:
        raise HFConfigError("HF_MODEL 환경변수가 비어 있습니다.")


# -----------------------------------------------------
# 4) LLM 호출 함수
# -----------------------------------------------------

def call_llm(user_prompt: str) -> str:
    """
    병동 스케줄 챗봇에서 사용하는 LLM 호출 함수.
    입력: user_prompt (string)
    출력: string (한국어 모델 응답)
    """

    _ensure_config()

    if not user_prompt or not user_prompt.strip():
        return "입력된 질문이 없습니다."

    # -----------------------------------------------------
    # 한국어로만 답변하도록 강제하는 System Prompt
    # DeepSeek-R1 hallucination 및 <think> 방지 설정
    # -----------------------------------------------------
    system_prompt = (
        "너는 병동 근무표 분석을 수행하는 전문 한국어 AI이다.\n"
        "반드시 지켜야 할 규칙:\n"
        "1) 모든 답변은 100% 자연스러운 한국어로 작성한다.\n"
        "2) <think>, 사고 과정, 중간 추론은 절대 출력하지 않는다.\n"
        "3) 제공된 데이터와 사용자 프롬프트 범위 밖의 내용은 추론하지 않는다.\n"
        "4) 근거가 없는 추론, 임의 가정, 과장, 추측은 절대 하지 않는다.\n"
        "5) 데이터가 부족하면 '해당 정보를 판단하기에 데이터가 부족합니다'라고 말한다.\n"
        "6) 논리적이고 정확하며 간결하게 설명한다.\n"
        "7) 스케줄 분석 시 '근무일수, 야간횟수, 연속근무, OFF간격' 같은 실제 제공된 통계만 활용한다.\n"
    )

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_MODEL,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_output_tokens": 512,
    }

    try:
        response = requests.post(HF_URL, headers=headers, json=payload, timeout=40)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"HF API 네트워크 오류: {e}")

    if response.status_code != 200:
        raise RuntimeError(f"HF API Error {response.status_code}: {response.text}")

    data = response.json()

    # -----------------------------------------------------
    # Responses API 파싱
    # -----------------------------------------------------
    try:
        outputs = data.get("output", [])
        if outputs:
            contents = outputs[0].get("content", [])
            for item in contents:
                if item.get("type") in ("output_text", "text"):
                    txt = item.get("text", "").strip()
                    if txt:
                        # 혹시 <think>가 들어와도 제거
                        return txt.replace("<think>", "").replace("</think>", "").strip()

        # Fallback
        if "output_text" in data:
            txt = data["output_text"]
            if isinstance(txt, str):
                return txt.strip()

    except Exception:
        return str(data)

    return str(data)

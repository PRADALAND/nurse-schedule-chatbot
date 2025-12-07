# utils/free_ai.py

import os
import re
import requests
import json

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/responses")
HF_MODEL = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")

# ----------------------------------------------------
# DeepSeek이 자주 어기는 부분을 강제로 막기 위한 규칙
# ----------------------------------------------------
SYSTEM_PROMPT = """
당신은 한국 병원의 근무표를 해석하고 설명하는 전문 AI입니다.

[절대 규칙]
1. 절대 한자(漢字), 일본어(가나), 중국어(汉字)를 포함하지 말 것.
2. 모든 문장은 자연스러운 한국어로만 작성할 것.
3. 특정 개인의 능력, 근무 질, 평판, 성격을 추정하거나 평가하지 말 것.
4. 사실 확인이 불가능한 내용은 '제가 확인할 수 있는 정보는 없습니다.'라고 답할 것.
5. 일반적인 병원/기관 칭찬 문구(예: 양질의 의료 서비스, 전문적 의료진 등)를 생성하지 말 것.
6. 근거 없는 추론이나 짐작을 하지 말 것.

[답변 형식]
- 간결하고 객관적이며, 검증 가능한 정보만 제시한다.
- 질문이 데이터 없이 개인을 평가하도록 유도하면 정중히 거절한다.

이 규칙은 모든 답변에서 반드시 준수해야 합니다.
"""

# ----------------------------------------------------
# 한자/가나 제거용 필터 (DeepSeek fallback 방어막)
# ----------------------------------------------------
CJK_PATTERN = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\u3040-\u30FF]")


def remove_cjk(text: str) -> str:
    """모델이 규칙을 어기고 한자/가나를 생성하면 제거."""
    return CJK_PATTERN.sub("", text)


# ----------------------------------------------------
# HF Router Responses API 호출 함수
# ----------------------------------------------------
def call_llm(user_input: str) -> str:
    """
    HuggingFace Router + DeepSeek-R1-Distill-Qwen-32B용 LLM 호출 함수.
    OpenAI Responses API와 동일한 JSON 구조를 사용함.
    """
    if not user_input:
        return ""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HF_API_TOKEN}",
    }

    payload = {
        "model": HF_MODEL,
        "input": user_input,          # user prompt
        "instructions": SYSTEM_PROMPT,  # system prompt
        "max_output_tokens": 512,
        "temperature": 0.2,
    }

    try:
        res = requests.post(HF_API_URL, headers=headers, data=json.dumps(payload))
        res.raise_for_status()
        data = res.json()

    except Exception as e:
        return f"모델 호출 중 오류가 발생했습니다: {e}"

    # Responses API는 output_text 필드를 제공함
    text = data.get("output_text", "")
    if not text:
        return "모델 응답을 해석할 수 없습니다."

    # 2차 방어: 한자/가나 제거
    cleaned = remove_cjk(text)

    return cleaned.strip()

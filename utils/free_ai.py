import os
import requests

HF_API_URL = os.getenv("HF_API_URL")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL")

SYSTEM_PROMPT = """
당신은 '근무 스케줄 분석 전문 AI'입니다.
개인 건강이나 위험을 추론하지 않으며, 스케줄 패턴 분석만 수행합니다.
친절하고 전문적이며 명확하게 설명합니다.
"""

def call_llm(user_input: str) -> str:
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        "max_tokens": 600
    }

    try:
        res = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        data = res.json()

        raw = data["choices"][0].get("message", {}).get("content", "")

        if "<think>" in raw:
            raw = raw.split("</think>")[-1].strip()

        return raw.strip() if raw else "응답을 생성하지 못했습니다."
    except Exception as e:
        return f"모델 호출 오류: {e}"

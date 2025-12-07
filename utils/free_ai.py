import os
import requests

HF_API_URL = os.getenv("HF_API_URL")  # e.g., https://router.huggingface.co/v1/responses
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")

SYSTEM_INSTRUCTION = """
당신은 병동 근무 패턴 분석을 수행하는 AI입니다.
개인 위험 진단은 하지 않으며, 근무표에서 파생되는 구조적 패턴, 업무량, 휴식 간격 등을 객관적 기준으로 서술합니다.
"""

def call_llm(user_query: str) -> str:
    if not HF_API_URL or not HF_API_TOKEN:
        return "HF API 환경변수가 설정되지 않았습니다."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_query}
        ],
        "max_tokens": 600,
        "temperature": 0.6
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        # HF router returns:
        # { "choices": [ { "message": { "content": "..."} } ] }
        if "choices" in data and len(data["choices"]) > 0:
            msg = data["choices"][0]["message"]["content"]
        else:
            msg = str(data)

        # remove <think> section if exists
        if "</think>" in msg:
            msg = msg.split("</think>")[-1].strip()

        return msg.strip()

    except Exception as e:
        return f"모델 호출 중 오류가 발생했습니다: {e}"

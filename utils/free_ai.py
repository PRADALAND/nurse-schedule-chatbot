# utils/free_ai.py

import os
import requests

HF_API_URL = os.getenv("HF_API_URL")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "")

SYSTEM = """
당신은 한국 병동의 근무 스케줄 분석을 도와주는 AI입니다.
개인의 건강 위험을 예측하거나 진단하지 말고,
근무 패턴, 야간 연속근무, 휴식 간격, 공정성 등 '스케줄 자체'만 분석하세요.
"""

def call_llm(query: str) -> str:
    if not HF_API_URL or not HF_API_TOKEN:
        return "HF API 환경변수가 설정되지 않았습니다."

    prompt = SYSTEM + "\n\n[사용자 질문]\n" + query

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 600,
            "temperature": 0.6,
            "do_sample": True
        }
    }

    try:
        res = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()

        # text-generation format
        if isinstance(data, list) and data and "generated_text" in data[0]:
            text = data[0]["generated_text"]
        else:
            text = str(data)

        # remove <think> blocks
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()

        return text.strip()

    except Exception as e:
        return f"모델 호출 오류: {e}"

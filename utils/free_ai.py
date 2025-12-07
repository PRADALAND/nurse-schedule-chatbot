# utils/free_ai.py

import os
import requests

# 환경변수 이름은 네가 쓰는 값에 맞게 바꾸면 됨
HF_API_URL = os.getenv("HF_API_URL")      # 예: "https://api-inference.huggingface.co/models/xxx"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # HF 토큰
HF_MODEL = os.getenv("HF_MODEL", "")      # 필요 없으면 안 써도 됨

SYSTEM_PROMPT = """
당신은 한국 병동에서 근무표를 분석하는 전문 AI입니다.
- 개인 건강 상태나 개인 질병 위험을 '예측'하거나 '진단'하지 않습니다.
- 대신 근무 패턴, 연속 야간 근무, 휴식 간격, 휴무 분포, 노동 강도와 같은
  스케줄 자체의 특성만 분석합니다.
- 법·지침에 근거한 피로 위험, 공정성 이슈를 객관적으로 설명합니다.
"""

def _build_prompt(user_input: str) -> str:
    return f"{SYSTEM_PROMPT.strip()}\n\n[사용자 질문]\n{user_input.strip()}\n"

def call_llm(user_input: str) -> str:
    """
    Hugging Face Inference API를 호출하여 답변을 생성하는 함수.
    1_Chatbot.py에서는 이 함수만 import해서 사용하면 된다.
    """
    if not HF_API_URL or not HF_API_TOKEN:
        return "HF_API_URL / HF_API_TOKEN 환경변수가 설정되지 않아 모델을 호출할 수 없습니다."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    prompt = _build_prompt(user_input)

    payload = {
        # text-generation 형식 엔드포인트 기준
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 700,
            "temperature": 0.5,
            "do_sample": True,
        }
    }

    try:
        res = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()

        # 예: [{"generated_text": "..."}] 형태
        if isinstance(data, list) and data and isinstance(data[0], dict):
            text = data[0].get("generated_text", "").strip()
        else:
            text = str(data)

        # 혹시 <think> 태그 같은 게 섞여 있으면 잘라내기
        if "<think>" in text and "</think>" in text:
            text = text.split("</think>")[-1].strip()

        return text or "모델이 빈 응답을 반환했습니다."

    except Exception as e:
        return f"모델 호출 중 오류가 발생했습니다: {e}"

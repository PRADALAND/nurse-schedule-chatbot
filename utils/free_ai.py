import os
import requests

HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_URL   = os.getenv("HF_API_URL")


def call_llm(prompt: str, max_tokens: int = 256, temperature: float = 0.3):
    """
    HuggingFace Router 기반 LLM 호출 함수.
    pages/1_Chatbot.py 등에서 import 해 사용한다.
    """

    if not HF_TOKEN:
        return "ERROR: HF_API_TOKEN not set in environment."

    if not HF_URL:
        return "ERROR: HF_API_URL not set in environment."

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
        }
    }

    try:
        r = requests.post(HF_URL, headers=headers, json=payload, timeout=20)

        # Router API 오류 처리
        if r.status_code == 404:
            return f"HF API Error 404: 모델을 찾을 수 없습니다. URL={HF_URL}"

        if r.status_code == 410:
            return "HF API Error 410: api-inference.huggingface.co는 더 이상 지원되지 않습니다. router.huggingface.co 를 사용하세요."

        if r.status_code >= 400:
            return f"HF API Error {r.status_code}: {r.text}"

        result = r.json()

        # Router 응답 구조 처리
        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]

        if isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]

        return str(result)

    except Exception as e:
        return f"HF API Exception: {e}"

import os
import requests

HF_TOKEN = os.getenv("HF_API_TOKEN")
HF_URL   = os.getenv("HF_API_URL", "https://router.huggingface.co/inference")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")


def call_llm(prompt: str, max_tokens: int = 256, temperature: float = 0.3):
    """
    HuggingFace Router API 기반 LLM 호출 함수.
    모델명은 payload 내부에 포함해야 하며 URL에 넣으면 404 오류가 발생한다.
    """

    if not HF_TOKEN:
        return "ERROR: HF_API_TOKEN not set in environment."

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_MODEL,       # 모델명은 여기!
        "input": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
        }
    }

    try:
        r = requests.post(HF_URL, headers=headers, json=payload, timeout=30)

        if r.status_code >= 400:
            return f"HF API Error {r.status_code}: {r.text}"

        data = r.json()

        # Router responses vary; handle all formats.
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]

        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]

        return str(data)

    except Exception as e:
        return f"HF API Exception: {e}"

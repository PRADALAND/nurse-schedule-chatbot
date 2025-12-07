# utils/free_ai.py
import os
import requests


HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = "https://router.huggingface.co/v1/responses"
HF_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"


def call_llm(prompt: str) -> str:
    """
    DeepSeek-R1-Distill-Qwen-32B 모델이 HF Router에서 반환하는
    모든 주요 응답 포맷을 지원하는 파서 포함.
    """

    if not HF_API_TOKEN:
        return "HF_API_TOKEN이 설정되어 있지 않습니다."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_MODEL,
        "input": prompt,
        "max_tokens": 512,
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"모델 호출 오류: {str(e)}"

    # ================================================
    # 1) HF Responses API 공식 포맷(output → choices → message → content)
    # ================================================
    try:
        if "output" in data and "choices" in data["output"]:
            choice = data["output"]["choices"][0]
            msg = choice.get("message", {})
            contents = msg.get("content", [])

            texts = []
            for block in contents:
                if isinstance(block, dict) and block.get("type") in ("output_text", "text"):
                    texts.append(block.get("text", ""))

            if texts:
                return "\n".join(texts).strip()
    except:
        pass

    # ================================================
    # 2) DeepSeek Distill 계열 (choices[].generated_text)
    # ================================================
    try:
        if "choices" in data and data["choices"]:
            first = data["choices"][0]
            if "generated_text" in first:
                return first["generated_text"].strip()
    except:
        pass

    # ================================================
    # 3) 일부 DeepSeek Distill 포맷 (output_text 단일필드)
    # ================================================
    if "output_text" in data:
        return data["output_text"].strip()

    # ================================================
    # 4) 모두 실패 → 원본 응답 출력
    # ================================================
    return f"모델 응답을 해석할 수 없습니다.\n원본 응답: {data}"

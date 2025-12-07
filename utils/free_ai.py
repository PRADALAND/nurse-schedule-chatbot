# utils/free_ai.py
import os
import requests

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = "https://router.huggingface.co/v1/responses"
HF_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"


def call_llm(prompt: str) -> str:

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
    # 1) DeepSeek Distill – 실제 응답 포맷 (너가 제공한 구조)
    # ================================================
    try:
        output = data.get("output", [])
        if isinstance(output, list) and len(output) > 0:
            first = output[0]

            if first.get("type") == "message":
                content_list = first.get("content", [])
                texts = []
                for c in content_list:
                    if c.get("type") == "output_text":
                        texts.append(c.get("text", ""))

                if texts:
                    return "\n".join(texts).strip()
    except:
        pass


    # ================================================
    # 2) 다른 DeepSeek fallback: choices[].generated_text
    # ================================================
    try:
        if "choices" in data and data["choices"]:
            first = data["choices"][0]
            if "generated_text" in first:
                return first["generated_text"].strip()
    except:
        pass


    # ================================================
    # 3) output_text 단독 존재
    # ================================================
    if "output_text" in data:
        return data["output_text"].strip()


    # ================================================
    # 4) 아무 것도 매칭되지 않을 때 원본 반환
    # ================================================
    return f"모델 응답을 해석할 수 없습니다.\n원본 응답: {data}"

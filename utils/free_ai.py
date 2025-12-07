# utils/free_ai.py
import os
import requests
import re

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_API_URL = "https://router.huggingface.co/v1/responses"
HF_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"


def clean_reasoning(text: str) -> str:
    """
    DeepSeek Distill 모델이 출력하는 reasoning leak 제거 필터.
    내부 독백, 다국어 노이즈 등을 최대한 제거하고 실제 답변만 남김.
    """

    # 1) DeepSeek의 내부 독백 패턴 제거
    patterns = [
        r"(?s)^.*?(?=Final Answer)",
        r"(?s)^.*?(?=Answer:)",
        r"(?s)^.*?(?=Therefore)",
        r"(?s)^.*?(?=In conclusion)",
        r"(?s)^.*?(?=결론)",
        r"(?s)^.*?(?=답변)",
    ]

    cleaned = text

    for p in patterns:
        new_cleaned = re.sub(p, "", cleaned)
        if new_cleaned != cleaned:
            cleaned = new_cleaned
            break

    # 2) DeepSeek 다국어 노이즈 제거
    cleaned = re.sub(r"[A-Za-zА-Яа-яЁёßçöüäœÆØø]+_[A-Za-z0-9]+", "", cleaned)

    # 3) 불필요한 줄바꿈 정리
    cleaned = cleaned.strip()

    return cleaned


def call_llm(prompt: str) -> str:
    """
    HF Responses API를 사용해 DeepSeek Distill 모델을 호출하고
    응답 파싱 + reasoning 제거까지 처리한 후 텍스트만 반환.
    """

    if not HF_API_TOKEN:
        return "HF_API_TOKEN이 설정되지 않았습니다."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_MODEL,
        "input": prompt,
        "max_tokens": 512,
    }

    # -------------------------
    # API 호출
    # -------------------------
    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"모델 호출 오류: {str(e)}"


    # ============================================================
    # 1) 너가 직접 제공한 실제 DeepSeek Distill 응답 구조 파싱
    # ============================================================
    try:
        output = data.get("output", [])
        if isinstance(output, list) and len(output) > 0:

            block = output[0]  # type=message
            content_list = block.get("content", [])

            texts = []
            for c in content_list:
                if c.get("type") == "output_text":
                    texts.append(c.get("text", ""))

            if texts:
                full_text = "\n".join(texts)
                return clean_reasoning(full_text)
    except Exception:
        pass


    # ============================================================
    # 2) DeepSeek fallback 형식 파싱 (choices[].generated_text)
    # ============================================================
    try:
        if "choices" in data and data["choices"]:
            g = data["choices"][0].get("generated_text")
            if g:
                return clean_reasoning(g)
    except Exception:
        pass


    # 마지막 수단: 원본 반환
    return f"모델 응답을 해석할 수 없습니다.\n원본 응답: {data}"

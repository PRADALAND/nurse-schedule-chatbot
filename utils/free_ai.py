# utils/free_ai.py
import os
import requests
import re

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_API_URL = "https://router.huggingface.co/v1/responses"
HF_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"


### ---------------------------------------
### 1) DeepSeek reasoning 제거
### ---------------------------------------
def clean_reasoning(text: str) -> str:
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

    cleaned = re.sub(r"[A-Za-zА-Яа-яЁёßçöüäœÆØø]+_[A-Za-z0-9]+", "", cleaned)
    return cleaned.strip()


### ---------------------------------------
### 2) DeepSeek 모델 호출 + 한국어 강제 시스템 프롬프트
### ---------------------------------------
def call_llm(prompt: str) -> str:

    if not HF_API_TOKEN:
        return "HF_API_TOKEN이 설정되지 않았습니다."

    ### 핵심: 모든 입력 앞에 시스템 지시 삽입
    system_instruction = (
        "당신은 간호 스케줄 분석 전문가입니다. "
        "항상 한국어로만 대답하십시오. "
        "영어 문장이나 내부 추론(생각 과정)은 절대 출력하지 마십시오. "
        "최종 결론만 간결하고 명확하게 한국어로 출력하십시오.\n\n"
        "사용자 질문:\n"
    )

    final_input = system_instruction + prompt

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_MODEL,
        "input": final_input,
        "max_tokens": 512,
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"모델 호출 오류: {str(e)}"


    # ----------------------------
    # 1) 너가 제공한 실제 output 구조
    # ----------------------------
    try:
        output = data.get("output", [])
        if isinstance(output, list) and len(output) > 0:
            block = output[0]
            content_list = block.get("content", [])

            texts = [c.get("text", "") for c in content_list if c.get("type") == "output_text"]
            if texts:
                return clean_reasoning("\n".join(texts))
    except:
        pass

    # ----------------------------
    # 2) fallback
    # ----------------------------
    try:
        if "choices" in data and data["choices"]:
            t = data["choices"][0].get("generated_text")
            if t:
                return clean_reasoning(t)
    except:
        pass

    return f"모델 응답 파싱 실패: {data}"

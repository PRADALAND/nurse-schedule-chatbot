# utils/free_ai.py

import os
import requests
import re

HF_TOKEN = os.getenv("HF_API_TOKEN") or os.getenv("HF_TOKEN")
HF_URL = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/responses")
HF_MODEL = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")


class HFConfigError(RuntimeError):
    pass


def _ensure_config():
    if not HF_TOKEN:
        raise HFConfigError("HF_API_TOKEN 또는 HF_TOKEN 환경변수가 없습니다.")
    if not HF_URL.startswith("http"):
        raise HFConfigError(f"HF_API_URL 형식 오류: {HF_URL}")
    if not HF_MODEL:
        raise HFConfigError("HF_MODEL이 비어 있습니다.")


def clean_llm_output(text: str) -> str:
    """LLM 출력에서 <think> 제거, 반복문장 차단."""
    if not text:
        return text

    # 1) <think> 전체 제거
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # 2) think, reasoning 따위가 나오면 제거
    forbidden = ["<think>", "</think>", "reasoning", "chain-of-thought"]
    for f in forbidden:
        text = text.replace(f, "")

    # 3) repeating 문장 패턴 제거 (예: 같은 문장 20번 반복)
    lines = text.split("\n")
    deduped = []
    seen = set()
    for ln in lines:
        if ln.strip() and ln.strip() not in seen:
            deduped.append(ln)
            seen.add(ln.strip())

    return "\n".join(deduped).strip()


def call_llm(user_prompt: str) -> str:
    _ensure_config()

    if not user_prompt.strip():
        return "질문이 비어 있습니다."

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    # THINK 금지 + 반복 억제 + 한국어 강제
    system_prompt = (
        "너는 한국 병동 스케줄 분석 AI다. "
        "최종 답변만 자연스러운 한국어로 출력하라. "
        "절대로 <think>, reasoning, 사고 과정, 내부 분석을 출력하지 마라. "
        "같은 문장을 반복하지 마라. "
        "계산 근거는 간결하게 요약해서만 말하라."
    )

    payload = {
        "model": HF_MODEL,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_output_tokens": 512,
        "temperature": 0.3,
    }

    try:
        resp = requests.post(HF_URL, headers=headers, json=payload, timeout=40)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"HF API 네트워크 오류: {e}")

    if resp.status_code != 200:
        raise RuntimeError(f"HF API Error {resp.status_code}: {resp.text}")

    data = resp.json()

    # output 추출
    outputs = data.get("output", [])
    answer = ""
    if outputs:
        contents = outputs[0].get("content", [])
        for c in contents:
            if c.get("type") in ("output_text", "text"):
                answer += c.get("text", "")

    # 후처리
    return clean_llm_output(answer)

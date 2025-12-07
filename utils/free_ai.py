# utils/free_ai.py
import os
import requests
import json

HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # Streamlit Secrets에 넣기
HF_API_URL = "https://router.huggingface.co/v1/responses"  # 너가 지정한 URL
HF_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"      # 너가 지금 사용 중인 모델


def call_llm(prompt: str) -> str:
    """
    Hugging Face Responses API v1 에 맞춰 DeepSeek-R1-Distill-Qwen-32B 모델을 호출한다.
    - prompt: 사용자 문자열
    - return: 모델 응답 문자열
    """

    if not HF_API_TOKEN:
        return "HF_API_TOKEN이 설정되어 있지 않습니다. Streamlit secrets 를 확인하세요."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    # HF Responses API는 'input' 필드를 사용해야 함 (messages 쓰면 400 확정)
    # 모델에 따라 'max_tokens' 또는 'max_new_tokens'가 통일되지 않아, HF Router는 둘 다 허용.
    payload = {
        "model": HF_MODEL,
        "input": prompt,
        "max_tokens": 512,
    }

    try:
        resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()

    except requests.HTTPError as http_err:
        # body 내용 일부를 반환해 디버깅 가능
        body = ""
        try:
            body = resp.text[:500]
        except:
            pass
        return f"[HTTP 오류] {resp.status_code}: {body}"

    except Exception as e:
        return f"[요청 실패] {str(e)}"

    # ------------------------------
    # 응답 Parsing (DeepSeek-R1-Distill 호환)
    # ------------------------------
    try:
        data = resp.json()

        # HF Responses API 표준 포맷:
        # {
        #   "id": "...",
        #   "output": {
        #     "choices": [
        #       {
        #         "message": {
        #            "role": "assistant",
        #            "content": [
        #               {"type": "output_text", "text": "..."}
        #            ]
        #         }
        #       }
        #     ]
        #   }
        # }

        if "output" in data and "choices" in data["output"]:
            choice = data["output"]["choices"][0]
            message = choice.get("message", {})
            contents = message.get("content", [])

            collected_texts = []
            for c in contents:
                if isinstance(c, dict) and c.get("type") in ("output_text", "text"):
                    collected_texts.append(c.get("text", ""))

            final_text = "\n".join(collected_texts).strip()
            if final_text:
                return final_text

    except Exception:
        pass

    # ------------------------------
    # Fallback (OpenAI 호환 응답 구조 대응)
    # ------------------------------
    try:
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"].strip()
    except:
        pass

    return "모델 응답을 해석할 수 없습니다. API 응답 구조가 예상과 다릅니다."

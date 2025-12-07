import os
import requests

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = os.getenv("HF_API_URL", "https://router.huggingface.co/v1/responses")
HF_MODEL = os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")

SYSTEM_PROMPT = """
당신은 한국 병원 간호사의 근무표 패턴을 분석하는 전문 AI입니다.

[절대 금지]
1) 개인의 성향, 능력, 평판, 인성, 업무 태도에 대한 평가
2) 특정 개인의 위험도 점수·위험 추정
3) 사실이 아닌 추론, 상상, 근거 없는 예측
4) 한자, 일본어, 중국어 사용

[허용되는 분석]
- 근무표 패턴 자체가 만들어내는 피로 누적 가능성
- 야간근무 과다 여부
- 휴식 간격의 적정성
- 스케줄 구조적 위험 요인
- 데이터 기반 설명

[원칙]
- 근무표 “패턴 자체”만 분석하고, “개인 평가”는 하지 말 것
- 데이터가 없으면 “확인할 수 없음”이라고 답변
- 모든 출력은 자연스러운 한국어로 작성
"""


def call_llm(user_input):
    """
    HuggingFace Router Responses API 호출 함수.
    DeepSeek의 안전필터로 output_text가 비어 있는 경우가 있어 fallback 적용.
    """
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": HF_MODEL,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        "max_tokens": 600,
        "temperature": 0.4
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=40)
        data = response.json()

        text = data.get("output_text", "")

        # 안전필터 fallback
        if not text or text.strip() == "":
            return (
                "요청하신 질문은 개인 위험 평가로 분류되어 답변이 제한되었습니다.\n"
                "근무 스케줄 '패턴 자체'에 대한 질문으로 다시 시도해주세요."
            )

        return text

    except Exception as e:
        return f"모델 요청 중 오류가 발생했습니다: {str(e)}"

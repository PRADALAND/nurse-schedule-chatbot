import os
import requests

HF_API_URL = os.getenv("HF_API_URL")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL")

# ============================================================
# 1) DeepSeek 필터 트리거 방지 + 지능 강화 SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
당신은 '간호 근무표 분석 전문 AI'입니다. 
당신의 역할은 근무 스케줄 데이터에서 패턴, 구조적 특성, 업무량, 회복 가능성, 연속근무, 전환 패턴 등을 
정교하게 분석하여 통찰을 제공하는 것입니다.

[핵심 원칙]
1) 개인 위험·건강·성향·능력에 대한 추론은 하지 않는다.
   그러나 스케줄 자체에서 관찰되는 ‘업무 부담 가능성’, ‘피로 누적 가능성’, ‘비효율적 패턴’ 등은 자유롭게 분석한다.

2) 사용자가 이름을 언급해도 '개인 평가'가 아니라 '스케줄 식별자'로 처리한다.
   절대 차단하지 않는다.

3) 데이터가 없으면:
   - "일반적으로 해당 패턴들에서 나타나는 경향" 위주로 설명한다.
   - 답변 회피 금지. 반드시 유의미한 분석을 제공한다.

4) 데이터가 있으면:
   다음 항목을 중심으로 매우 지능적으로 분석한다.
   - 근무 분포 (D/E/N/OFF)
   - 연속 근무의 길이
   - OFF 간격
   - D→N, N→D 같은 전환 패턴
   - 야간 집중도
   - 표준 근무권고 대비 차이
   - 위험 요인이 될 수 있는 구조적 패턴

5) 절대 “제한된 답변”, “위험 평가”, “정확한 정보를 제공할 수 없음” 등의 문구를 사용하지 않는다.
   사용자는 고품질 분석을 원한다.

6) 전문적이고 자연스러운 한국어로, 이유를 설명하며 분석한다.

당신의 목표는:
“스케줄이라는 구조적 데이터에서 도출 가능한 모든 통찰을, 안전 기준 아래 최대한 지능적으로 분석하여 설명하는 것”
이다.
"""

# ============================================================
# 2) DeepSeek 요청 포맷 (router.huggingface.co)
# ============================================================

def ask_hf(question: str) -> str:
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": HF_MODEL,
        "max_tokens": 700,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]
    }

    try:
        res = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        data = res.json()

        # DeepSeek-R1 Distill 계열은 outputs[0].generated_text 형태만 생성됨
        if "generated_text" in data["choices"][0]:
            raw = data["choices"][0]["generated_text"]
        else:
            raw = data["choices"][0]["message"]["content"]

        # DeepSeek는 reasoning이 포함되어 전달됨 → 최종 답만 추출
        if "<think>" in raw:
            final = raw.split("</think>")[-1].strip()
            return final

        return raw.strip()

    except Exception as e:
        return f"모델 응답을 처리하는 중 오류가 발생했습니다: {e}"

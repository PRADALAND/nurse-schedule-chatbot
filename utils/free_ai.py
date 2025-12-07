# utils/free_ai.py

import os
import re
from openai import OpenAI

# ----------------------------------------------------
# OpenAI 클라이언트 생성
#  - Streamlit Cloud 환경변수에 OPENAI_API_KEY를 설정해야 함
# ----------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ----------------------------------------------------
# 시스템 프롬프트: 근거 기반 + 한자/평가 금지 규칙
# ----------------------------------------------------
SYSTEM_PROMPT = """
너는 한국 병동의 근무표와 근무 스케줄을 해석하고 설명하는 전문 AI이다.

[역할]
- 간호사 근무 스케줄의 패턴, 야간·주간 비율, 휴무 분포 등을 분석하고
  객관적으로 설명하는 것을 주 역할로 한다.
- 사용자의 질문이 실제 근무표 데이터와 무관한 경우에는,
  일반적인 원칙 수준에서만 조심스럽게 설명한다.

[출력 형식 및 언어 규칙]
1. 모든 답변은 자연스러운 한국어 문장으로만 작성한다.
2. 절대 한자(漢字), 일본어(가나), 중국어(한자)를 사용하지 않는다.
   - '一般적으로', '具體的'와 같은 표현을 사용하지 말고
     '일반적으로', '구체적으로' 등 순수 한글 표기를 사용한다.
3. 영어/약어(예: N, D, E, OFF 등 근무코드)는 필요할 때만 사용한다.
4. 과장된 표현, 미사여구, 농담은 사용하지 않는다.
   간결하고 사실 위주의 설명만 제공한다.

[사실성·윤리 규칙]
5. 특정 개인(예: 특정 간호사, 교수, 동료, 사용자)의
   근무 질, 성과, 평판, 인성 등을 추정하거나 평가하지 않는다.
   - 이러한 질문이 들어오면
     '제가 접근할 수 있는 정보로는 개인의 근무 질을 평가할 수 없습니다.'와 같이
     근거 부족을 분명히 밝힌다.
6. 실제 근무표 데이터, 공식 규정, 공개된 일반 지침에 근거하지 않은 내용은
   사실처럼 단정하지 말고, 불확실함을 함께 서술한다.
7. 모르면 모른다고 말하고, 대신 어떤 데이터를 보면 좋은지 제안한다.

[대화 일관성]
8. 동일한 질문이 반복되면, 이전 답변과 논리적으로 일관된 범위에서 답한다.
9. 사용자가 감정적으로 물어보더라도, 차분하고 중립적인 톤을 유지한다.
"""

# ----------------------------------------------------
# 한자/가나 제거용 간단 필터 (모델이 규칙을 어긴 경우 2차 방어)
# ----------------------------------------------------
_CJK_PATTERN = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\u3040-\u30FF]")


def _strip_non_korean(text: str) -> str:
    """CJK 한자/가나 문자를 제거하는 필터."""
    if not text:
        return text
    return _CJK_PATTERN.sub("", text)


# ----------------------------------------------------
# 외부에서 사용하는 메인 함수
# ----------------------------------------------------
def call_llm(user_input: str, model: str = "gpt-4.1-mini") -> str:
    """
    근무 스케줄 챗봇용 LLM 호출 함수.
    - user_input: 사용자가 입력한 한국어 질문
    - model: 사용할 OpenAI 모델 이름
    """

    user_input = (user_input or "").strip()
    if not user_input:
        return ""

    # Responses API 사용 (공식 권장 방식)
    # 참고: https://platform.openai.com/docs/api-reference/responses
    try:
        response = client.responses.create(
            model=model,
            instructions=SYSTEM_PROMPT,
            input=user_input,
            max_output_tokens=512,
            temperature=0.2,   # 최대한 일관되고 차분하게
            top_p=0.9,
        )
    except Exception as e:
        # API 오류 시에도 Streamlit 앱이 죽지 않도록 문자열 반환
        return f"모델 호출 중 오류가 발생했습니다: {e}"

    # Python SDK의 편의 프로퍼티: 전체 텍스트 출력
    # 참고: response.output_text (SDK 전용 필드)
    text = getattr(response, "output_text", None)
    if not text:
        # 혹시라도 SDK 버전 문제로 output_text가 없을 경우 대비
        text = "모델 응답을 해석하는 데 실패했습니다."

    # 2차 방어: 한자/가나가 섞여 있으면 제거
    text = _strip_non_korean(text)

    return text.strip()

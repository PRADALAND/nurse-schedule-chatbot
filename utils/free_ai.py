# utils/free_ai.py
import os
import json
from datetime import date
from typing import List, Dict, Any, Optional

import requests
import pandas as pd


def _default_parse(query: str, nurse_names: List[str], date_min: date, date_max: date) -> Dict[str, Any]:
    """
    LLM을 쓰지 않을 때 사용할 기본 파서.
    - 간단한 키워드만 보고 기간을 대략적으로 추정
    - 간호사 이름은 매칭되지 않으면 None
    """
    q = query.strip()

    # 1) 간호사 이름 단순 매칭 (완전 일치만)
    target_nurse: Optional[str] = None
    for name in nurse_names:
        if name and name in q:
            target_nurse = name
            break

    # 2) 기간 추정 (매우 단순)
    #   - "이번달"이 들어가면 전체 date_min~date_max
    #   - "지난주", "이번주" 같은 건 아직 단순화
    start = date_min
    end = date_max

    if "이번달" in q or "이 달" in q:
        start, end = date_min, date_max
    # 더 세분화하고 싶으면 여기 추가

    return {
        "nurse_name": target_nurse,        # 없으면 None
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "question_type": "summary",        # 지금은 요약만 지원
    }


def _call_hf_llm(prompt: str) -> str:
    """
    HuggingFace Inference API에 text-generation 요청.
    - HF_API_TOKEN 환경변수에 토큰이 있어야 실제 호출 가능.
    - HF_API_URL이 지정되어 있지 않으면 Qwen2.5 0.5B instruct 엔드포인트 예시 사용.
    """
    token = os.getenv("HF_API_TOKEN")
    if not token:
        raise RuntimeError("HF_API_TOKEN이 설정되어 있지 않습니다.")

    url = os.getenv(
        "HF_API_URL",
        "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-0.5B-Instruct",
    )

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.1,
        },
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # 모델에 따라 응답 포맷이 다를 수 있음.
    # 가장 일반적인 text-generation 포맷 기준으로 처리.
    if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
        return data[0]["generated_text"]
    # 다른 포맷이면 전체를 문자열로 덤프
    return json.dumps(data, ensure_ascii=False)


def analyze_query_free(
    query: str,
    df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    사용자 질의를 해석하여:
      - nurse_name (또는 None)
      - start_date, end_date (YYYY-MM-DD 문자열)
      - question_type (예: summary, night_focus 등)
    를 반환한다.

    1순위: HF LLM(Qwen 등)을 사용해 JSON을 생성
    2순위: HF 토큰이 없으면 _default_parse() 규칙 기반 해석
    """
    # 스케줄 전체 메타데이터
    if "date" not in df.columns:
        raise ValueError("df에 'date' 컬럼이 필요합니다.")
    date_min = df["date"].min().date() if isinstance(df["date"].min(), pd.Timestamp) else df["date"].min()
    date_max = df["date"].max().date() if isinstance(df["date"].max(), pd.Timestamp) else df["date"].max()

    nurse_names = sorted(
        [str(x) for x in df["nurse_name"].dropna().unique().tolist()]
    ) if "nurse_name" in df.columns else []

    # HF 토큰이 없으면 규칙 기반 파서만 사용
    if not os.getenv("HF_API_TOKEN"):
        return _default_parse(query, nurse_names, date_min, date_max)

    # HF LLM 프롬프트 설계
    system_instruction = (
        "너는 간호사 스케줄 질의를 분석하는 어시스턴트이다. "
        "입력된 한국어 질문과 간호사 이름 목록, 가능한 날짜 범위를 보고, "
        "반드시 JSON 한 덩어리만 반환해야 한다. "
        '형식은 다음과 같다: '
        '{"nurse_name": <또는 null>, "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "question_type": "summary"} '
        "question_type은 지금은 무조건 'summary'로 해도 좋다."
    )

    prompt = (
        f"{system_instruction}\n\n"
        f"가능한 간호사 이름 목록: {nurse_names}\n"
        f"전체 스케줄 기간: {date_min.isoformat()} ~ {date_max.isoformat()}\n\n"
        f"질문: {query}\n\n"
        "위 정보를 바탕으로 JSON만 출력해라."
    )

    try:
        raw = _call_hf_llm(prompt)
        # 가장 처음 '{' 부터 마지막 '}' 까지를 JSON으로 간주
        start_idx = raw.find("{")
        end_idx = raw.rfind("}")
        if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
            raise ValueError("JSON 구간을 찾지 못함")

        json_str = raw[start_idx : end_idx + 1]
        parsed = json.loads(json_str)

        # 최소 필드 검증 및 보정
        nurse_name = parsed.get("nurse_name")
        if nurse_name not in nurse_names:
            nurse_name = None

        start_s = parsed.get("start_date", date_min.isoformat())
        end_s = parsed.get("end_date", date_max.isoformat())

        return {
            "nurse_name": nurse_name,
            "start_date": start_s,
            "end_date": end_s,
            "question_type": parsed.get("question_type", "summary"),
        }
    except Exception:
        # LLM 호출 또는 파싱 실패 시, 규칙 기반으로 fallback
        return _default_parse(query, nurse_names, date_min, date_max)

# utils/analysis_log.py
import os
import csv
import json
from datetime import datetime
from typing import Any, Dict, List

LOG_FILE = "analysis_logs.csv"


def log_analysis(query: str, response: str, meta: Dict[str, Any] | None = None) -> None:
    """
    사용자 질의와 시스템 응답, 부가 메타데이터를 CSV 파일에 로깅한다.
    Streamlit Cloud에서도 작동하도록 로컬 파일 기반으로 구현.
    """
    meta = meta or {}
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "query": query,
        "response": response,
        "meta": json.dumps(meta, ensure_ascii=False),
    }

    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def fetch_logs(limit: int = 200) -> List[Dict[str, str]]:
    """
    최근 로그를 최대 limit개까지 반환한다.
    AI 분석 대시보드 페이지(5_AI_Analytics.py)에서 사용.
    """
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 최신 순으로 limit개
    return rows[-limit:]

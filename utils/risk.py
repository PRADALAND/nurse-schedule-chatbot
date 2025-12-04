import pandas as pd

# 총점 기준 위험도 구간 (예시값, 필요 시 조정 가능)
RISK_LEVELS = {
    "LOW": (0, 3),
    "MODERATE": (4, 7),
    "HIGH": (8, 100),
}


def _score_consecutive_working_days(cw: int) -> int:
    # 엑셀 기준: 6=Critical, 5=Moderate, 4=Low, ≤3 No risk
    if cw >= 6:
        return 3
    if cw == 5:
        return 2
    if cw == 4:
        return 1
    return 0


def _score_consecutive_nights(cn: int) -> int:
    # 엑셀 기준: 5=Critical, 4=Moderate, 3=Low, ≤2 No risk
    if cn >= 5:
        return 3
    if cn == 4:
        return 2
    if cn == 3:
        return 1
    return 0


def _score_staffing(diff: int) -> int:
    # 기준 인원 - 실제 인원이 2 이상이면 Critical, 1이면 Moderate, 0 이하면 No risk
    if diff >= 2:
        return 3
    if diff == 1:
        return 2
    return 0


def _score_quick_return(flag: bool) -> int:
    # ED/N quick return은 Critical 패턴으로 간주 → 3점
    return 3 if bool(flag) else 0


def compute_patient_safety_risk(row: pd.Series) -> int:
    """
    환자안전 관점 위험도 점수.
    엑셀 '환자안전' 시트 정의를 코드로 옮긴 것:
      - ED_quick_return
      - N_quick_return
      - consecutive_working_days
      - consecutive_night_shifts
      - staffing_diff
    """
    score = 0
    score += _score_quick_return(row.get("ED_quick_return", False))
    score += _score_quick_return(row.get("N_quick_return", False))
    score += _score_consecutive_working_days(int(row.get("consecutive_working_days", 0)))
    score += _score_consecutive_nights(int(row.get("consecutive_night_shifts", 0)))
    score += _score_staffing(int(row.get("staffing_diff", 0)))
    return int(score)


def add_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    환자안전 기반 위험도 점수를 DataFrame에 추가.
    - patient_safety_risk
    - overall_risk_score (현재는 동일 값으로 사용)
    """
    df = df.copy()
    df["patient_safety_risk"] = df.apply(compute_patient_safety_risk, axis=1)
    df["overall_risk_score"] = df["patient_safety_risk"].astype(int)
    return df


def risk_level(score: int) -> str:
    for level, (lo, hi) in RISK_LEVELS.items():
        if lo <= score <= hi:
            return level
    return "HIGH"

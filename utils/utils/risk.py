import pandas as pd

RISK_LEVELS = {
    "LOW": (0, 2),
    "MODERATE": (3, 5),
    "HIGH": (6, 100),
}


def compute_fatigue_risk(row: pd.Series) -> int:
    """
    피로도 점수 예시.
    ※ 임상 근거 기반이 아니라, 설명용 규칙이므로 실제 연구/서비스 사용 전에는
      반드시 별도의 근거 정리와 검증이 필요하다.
    """
    score = 0

    # 연속 근무일수
    cw = row.get("consecutive_working_days", 0)
    if cw >= 6:
        score += 3
    elif cw >= 4:
        score += 2
    elif cw >= 2:
        score += 1

    # 연속 야간
    cn = row.get("consecutive_night_shifts", 0)
    if cn >= 3:
        score += 3
    elif cn == 2:
        score += 2
    elif cn == 1:
        score += 1

    # 야간 후 데이 (quick return의 proxy)
    if row.get("prev_shift_type") == "NIGHT" and row.get("shift_type") == "DAY":
        score += 2

    # 주말 근무
    if bool(row.get("weekend_flag")) and row.get("shift_type") != "OFF":
        score += 1

    return int(score)


def compute_acuity_risk(row: pd.Series) -> int:
    """
    환자 중증도(acuity)에 기반한 위험도는 스케줄 데이터만으로 계산 불가하므로,
    현재는 0으로 두고, 향후 환자 acuity 데이터 연동 시 확장한다.
    """
    return 0


def compute_mismatch_risk(row: pd.Series) -> int:
    """
    간호사 선호(preferences)와 실제 배치 간 불일치 위험도.
    현재 예시에서는 선호 데이터가 없으므로 0으로 두고,
    향후 preferred_shift_types, preferred_off_days 등의 컬럼이 추가되면
    이 함수 내에서 점수를 계산한다.
    """
    return 0


def add_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    피로도/위험도 관련 피처를 DataFrame에 추가한다.
    - fatigue_risk
    - acuity_risk
    - mismatch_risk
    - overall_risk_score
    """
    df = df.copy()
    df["fatigue_risk"] = df.apply(compute_fatigue_risk, axis=1)
    df["acuity_risk"] = df.apply(compute_acuity_risk, axis=1)
    df["mismatch_risk"] = df.apply(compute_mismatch_risk, axis=1)
    df["overall_risk_score"] = (
        df["fatigue_risk"] + df["acuity_risk"] + df["mismatch_risk"]
    ).astype(int)
    return df


def risk_level(score: int) -> str:
    for level, (lo, hi) in RISK_LEVELS.items():
        if lo <= score <= hi:
            return level
    return "HIGH"

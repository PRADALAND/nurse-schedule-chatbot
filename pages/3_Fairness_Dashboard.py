import pandas as pd


REQUIRED_COLS = ["nurse_name", "shift_type", "date"]


def validate_input(df):
    """필수 컬럼 존재 여부 검증"""
    for col in REQUIRED_COLS:
        if col not in df.columns:
            raise KeyError(f"필요한 컬럼 '{col}' 이(가) 존재하지 않습니다.")
    return True


def compute_min_off_interval(sub):
    """OFF 간격 계산 (없으면 0)"""
    off_dates = sub[sub["shift_type"] == "OFF"]["date"].sort_values()
    if len(off_dates) < 2:
        return 0

    intervals = off_dates.diff().dt.days.dropna()
    return int(intervals.min()) if not intervals.empty else 0


def compute_fairness_table(df):
    """
    공정성 분석 핵심 함수.
    최소 공정성 컬럼들을 생성하여 DataFrame 반환.
    """

    # 안전장치: 필수 컬럼 검증
    validate_input(df)

    result_rows = []

    # nurse_name 그룹별 계산
    for nurse, sub in df.groupby("nurse_name"):
        sub = sub.copy()

        # 총 OFF / NIGHT 일수
        total_off = int((sub["shift_type"] == "OFF").sum())
        total_night = int((sub["shift_type"] == "NIGHT").sum())

        # OFF 간격
        min_off_interval = compute_min_off_interval(sub)

        # placeholder 값들 — 실제 규칙 기반 계산으로 교체 가능
        pref_match_ratio = 0.5
        level_night_ratio = 1.0
        level_workingdays_ratio = 1.0

        # 임시 fairness score: 반드시 존재하도록 설정
        fairness_score = (
            1.0
            - (total_night * 0.01)
            - (total_off * 0.005)
            + (pref_match_ratio * 0.1)
        )

        row = {
            "nurse_name": nurse,
            "fairness_score": float(fairness_score),
            "pref_match_ratio": float(pref_match_ratio),
            "total_off_days": total_off,
            "total_night_days": total_night,
            "min_off_interval": int(min_off_interval),
            "level_night_ratio": float(level_night_ratio),
            "level_workingdays_ratio": float(level_workingdays_ratio),
        }

        result_rows.append(row)

    fair_df = pd.DataFrame(result_rows)

    # 반드시 컬럼이 생성되었는지 최종 검사
    REQUIRED_OUTPUTS = [
        "nurse_name",
        "fairness_score",
        "pref_match_ratio",
        "total_off_days",
        "total_night_days",
        "min_off_interval",
        "level_night_ratio",
        "level_workingdays_ratio",
    ]

    for col in REQUIRED_OUTPUTS:
        if col not in fair_df.columns:
            raise RuntimeError(f"공정성 분석 출력에 '{col}' 생성 실패")

    return fair_df


def compute_fairness_stats(fair_df):
    """병동 전체 공정성 지표 요약 계산."""
    if fair_df is None or fair_df.empty:
        return {}

    return {
        "fairness_score_std": fair_df["fairness_score"].std(),
        "avg_pref_match_ratio": fair_df["pref_match_ratio"].mean(),
        "total_night_std": fair_df["total_night_days"].std(),
        "total_off_std": fair_df["total_off_days"].std(),
    }

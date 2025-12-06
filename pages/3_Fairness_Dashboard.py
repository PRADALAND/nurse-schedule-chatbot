import pandas as pd


def compute_fairness_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    간단한 규칙 기반 공정성 테이블 생성.
    최소한 다음 컬럼을 항상 만들어서 반환한다.

    - nurse_name
    - fairness_score
    - pref_match_ratio
    - total_off_days
    - total_night_days
    - min_off_interval
    - level_night_ratio
    - level_workingdays_ratio
    """

    if df is None or df.empty:
        return pd.DataFrame()

    # date 컬럼은 datetime으로 맞춰 둔다.
    if "date" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

    rows = []

    # 간호사별 그룹
    for nurse, sub in df.groupby("nurse_name"):
        sub = sub.copy().sort_values("date")

        # 기본 지표
        total_off = int((sub["shift_type"] == "OFF").sum())
        total_night = int((sub["shift_type"] == "NIGHT").sum())

        # OFF 간격
        off_dates = sub.loc[sub["shift_type"] == "OFF", "date"]
        if len(off_dates) >= 2:
            intervals = off_dates.diff().dt.days.dropna()
            min_off_interval = int(intervals.min()) if not intervals.empty else 0
        else:
            min_off_interval = 0

        # placeholder 지표 (나중에 엑셀 규칙으로 교체 가능)
        pref_match_ratio = 0.5
        level_night_ratio = 1.0
        level_workingdays_ratio = 1.0

        # 임시 공정성 점수 (단조로운 가중합)
        fairness_score = (
            1.0
            - total_night * 0.01
            - total_off * 0.005
            + pref_match_ratio * 0.1
        )

        rows.append(
            {
                "nurse_name": nurse,
                "fairness_score": float(fairness_score),
                "pref_match_ratio": float(pref_match_ratio),
                "total_off_days": total_off,
                "total_night_days": total_night,
                "min_off_interval": min_off_interval,
                "level_night_ratio": float(level_night_ratio),
                "level_workingdays_ratio": float(level_workingdays_ratio),
            }
        )

    fair_df = pd.DataFrame(rows)

    return fair_df


def compute_fairness_stats(fair_df: pd.DataFrame) -> dict:
    """병동 전체 공정성 지표 요약."""
    if fair_df is None or fair_df.empty:
        return {}

    return {
        "fairness_score_std": float(fair_df["fairness_score"].std()),
        "avg_pref_match_ratio": float(fair_df["pref_match_ratio"].mean()),
        "total_night_std": float(fair_df["total_night_days"].std()),
        "total_off_std": float(fair_df["total_off_days"].std()),
    }

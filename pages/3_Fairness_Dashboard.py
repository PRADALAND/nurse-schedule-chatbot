import pandas as pd

def compute_fairness_table(df):
    """
    공정성 분석을 위해 필요한 최소 컬럼을 생성하는 기본 버전.
    실제 로직은 이후 엑셀 규칙 기반으로 교체하면 됨.
    """

    result = []

    for nurse, sub in df.groupby("nurse_name"):
        sub = sub.copy()

        # 기본 지표
        total_off = (sub["shift_type"] == "OFF").sum()
        total_night = (sub["shift_type"] == "NIGHT").sum()

        # 최소 OFF 간격
        off_dates = sub[sub["shift_type"] == "OFF"]["date"].sort_values()
        if len(off_dates) >= 2:
            intervals = (off_dates.diff().dt.days.dropna())
            min_off_interval = int(intervals.min()) if not intervals.empty else 0
        else:
            min_off_interval = 0

        # placeholder 값들
        pref_match_ratio = 0.5
        level_night_ratio = 1.0
        level_workingdays_ratio = 1.0

        # 임시 fairness 계산
        fairness_score = (
            1.0
            - (total_night * 0.01)
            - (total_off * 0.005)
            + (pref_match_ratio * 0.1)
        )

        result.append({
            "nurse_name": nurse,
            "fairness_score": fairness_score,
            "pref_match_ratio": pref_match_ratio,
            "total_off_days": total_off,
            "total_night_days": total_night,
            "min_off_interval": min_off_interval,
            "level_night_ratio": level_night_ratio,
            "level_workingdays_ratio": level_workingdays_ratio,
        })

    return pd.DataFrame(result)


def compute_fairness_stats(fair_df):
    """병동 전체 공정성 지표 요약."""
    if fair_df is None or fair_df.empty:
        return {}

    stats = {
        "fairness_score_std": fair_df["fairness_score"].std(),
        "avg_pref_match_ratio": fair_df["pref_match_ratio"].mean(),
        "total_night_std": fair_df["total_night_days"].std(),
        "total_off_std": fair_df["total_off_days"].std(),
    }

    return stats

import pandas as pd

def compute_fairness_table(df):
    """
    공정성 분석을 위한 기본 컬럼 7개를 '절대 누락 없이' 생성하는 안전 버전.
    입력 df는 최소 nurse_name, date, shift_type 의 3개 컬럼만 있으면 동작한다.
    """
    
    # 입력 검증
    required = ["nurse_name", "shift_type", "date"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"compute_fairness_table: 입력 데이터에 필요한 컬럼이 없습니다: {missing}")

    result = []

    for nurse, sub in df.groupby("nurse_name"):
        sub = sub.copy().sort_values("date")

        # 1) OFF 일수
        total_off = (sub["shift_type"] == "OFF").sum()

        # 2) NIGHT 일수
        total_night = (sub["shift_type"] == "NIGHT").sum()

        # 3) 최소 OFF 간격
        off_dates = sub[sub["shift_type"] == "OFF"]["date"]
        if len(off_dates) >= 2:
            diff_days = off_dates.diff().dt.days.dropna()
            min_off_interval = int(diff_days.min()) if not diff_days.empty else 0
        else:
            min_off_interval = 0

        # 4) placeholder — 선호 패턴 반영률(나중에 로직 넣으면 됨)
        pref_match_ratio = 0.0

        # 5) 연차 대비 야간 근무 비율 (placeholder)
        level_night_ratio = float(total_night)

        # 6) 연차 대비 근무일 비율 (placeholder)
        total_working = len(sub[sub["shift_type"] != "OFF"])
        level_workingdays_ratio = float(total_working)

        # 7) 공정성 점수 — 최소한 NaN 되지 않도록 더미 산식 생성
        fairness_score = (
            1.0
            - (total_night * 0.01)
            + (total_off * 0.001)
            - (min_off_interval * 0.001)
        )

        result.append({
            "nurse_name": nurse,
            "fairness_score": float(fairness_score),
            "pref_match_ratio": float(pref_match_ratio),
            "total_off_days": int(total_off),
            "total_night_days": int(total_night),
            "min_off_interval": int(min_off_interval),
            "level_night_ratio": float(level_night_ratio),
            "level_workingdays_ratio": float(level_workingdays_ratio),
        })

    return pd.DataFrame(result)

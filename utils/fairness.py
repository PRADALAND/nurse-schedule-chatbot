import pandas as pd


def compute_fairness_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    스케줄 df에서 간호사별 공정성 지표를 계산하여 반환한다.

    요구되는 최소 컬럼:
    - nurse_name
    - shift_type
    - date
    (그 외 컬럼은 없어도 동작함)
    """
    if df is None or df.empty:
        return pd.DataFrame(
            columns=[
                "nurse_name",
                "fairness_score",
                "pref_match_ratio",
                "total_off_days",
                "total_night_days",
                "min_off_interval",
                "level_night_ratio",
                "level_workingdays_ratio",
            ]
        )

    required = ["nurse_name", "shift_type", "date"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"compute_fairness_table: 필수 컬럼이 없습니다: {missing}")

    result_rows = []

    for nurse, sub in df.groupby("nurse_name"):
        sub = sub.copy().sort_values("date")

        # 기본 카운트
        total_off = int((sub["shift_type"] == "OFF").sum())
        total_night = int((sub["shift_type"] == "NIGHT").sum())
        total_working = int((sub["shift_type"] != "OFF").sum())

        # 최소 OFF 간격
        off_dates = sub.loc[sub["shift_type"] == "OFF", "date"].sort_values()
        if len(off_dates) >= 2:
            intervals = off_dates.diff().dt.days.dropna()
            min_off_interval = int(intervals.min()) if not intervals.empty else 0
        else:
            min_off_interval = 0

        # 선호 반영율(현재는 placeholder, 나중에 엑셀 규칙으로 교체)
        pref_match_ratio = 0.5

        # 연차 기반 비율(placeholder) - 현재는 단순 비율
        level_night_ratio = float(total_night) / max(total_working, 1)
        level_workingdays_ratio = float(total_working) / max(len(sub), 1)

        # 간단한 공정성 점수 (값이 작을수록 불공정하다고 가정)
        # - 야간 많음: 불리
        # - OFF 부족: 불리
        # - OFF 간격 짧음: 불리
        fairness_score = (
            1.0
            - 0.02 * total_night
            - 0.01 * max(0, 8 - total_off)
            - 0.01 * max(0, 2 - min_off_interval)
        )

        result_rows.append(
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

    fair_df = pd.DataFrame(result_rows)
    return fair_df


def compute_fairness_stats(fair_df: pd.DataFrame) -> dict:
    """
    병동 전체 공정성 요약 지표.
    - 기존 app.py에서 쓰는 키들(night_std, weekend_std, night_ratio_std, weekend_ratio_std, avg_mean_overall_risk)
    - 새 Fairness Dashboard에서 쓰는 키들(fairness_score_std, avg_pref_match_ratio, total_night_std, total_off_std)
    를 모두 포함하도록 통합.
    """
    if fair_df is None or fair_df.empty:
        return {}

    stats = {}

    # 공정성 점수/선호 반영율/야간·OFF 분포
    stats["fairness_score_std"] = fair_df["fairness_score"].std(skipna=True) or 0.0
    stats["avg_pref_match_ratio"] = fair_df["pref_match_ratio"].mean(skipna=True) or 0.0
    stats["total_night_std"] = fair_df["total_night_days"].std(skipna=True) or 0.0
    stats["total_off_std"] = fair_df["total_off_days"].std(skipna=True) or 0.0

    # 기존 메인 페이지에서 쓰는 이름들과 맞추기 위한 매핑
    stats["night_std"] = stats["total_night_std"]
    stats["weekend_std"] = 0.0  # 아직 weekend 기반 공정성은 계산하지 않음
    stats["night_ratio_std"] = fair_df["level_night_ratio"].std(skipna=True) or 0.0
    stats["weekend_ratio_std"] = 0.0  # 아직 weekend 기반 비율 없음
    stats["avg_mean_overall_risk"] = 0.0  # 필요 시 나중에 overall_risk_score 기반으로 채울 수 있음

    return stats


def generate_fairness_narrative(fair_df: pd.DataFrame, nurse_name: str) -> str:
    """
    챗봇 탭에서 사용하는 공정성 설명용 텍스트.
    fairness_df와 nurse_name을 받아 사람이 읽을 수 있는 요약을 생성.
    """
    if fair_df is None or fair_df.empty:
        return "공정성 분석 결과가 없습니다."

    row = fair_df[fair_df["nurse_name"] == nurse_name]
    if row.empty:
        return f"{nurse_name}님의 공정성 분석 결과가 없습니다."

    r = row.iloc[0]

    lines = []
    lines.append(f"{nurse_name}님의 근무 공정성 분석 요약입니다.")
    lines.append(f"- 공정성 점수(fairness score): {r['fairness_score']:.3f}")

    # OFF
    lines.append(
        f"- 총 OFF 일수: {int(r['total_off_days'])}일, "
        f"Night 근무 일수: {int(r['total_night_days'])}일"
    )
    lines.append(f"- 최소 OFF 간격: {int(r['min_off_interval'])}일")

    # 선호 반영율
    lines.append(
        f"- 선호 근무 패턴 반영률(placeholder): {r['pref_match_ratio'] * 100:.1f}%"
    )

    # 간단한 해석
    if r["fairness_score"] < fair_df["fairness_score"].median():
        lines.append(
            "- 병동 평균에 비해 공정성 점수가 다소 낮아, 상대적으로 불리한 근무 배치일 가능성이 있습니다."
        )
    else:
        lines.append(
            "- 공정성 점수는 병동 평균 이상으로, 상대적으로 균형 잡힌 근무 배치에 가까운 편입니다."
        )

    lines.append(
        "※ 본 평가는 연구/모니터링 목적의 참고 지표이며, 인사평가나 징계의 직접 근거로 사용해서는 안 됩니다."
    )

    return "\n".join(lines)

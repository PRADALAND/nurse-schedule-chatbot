import pandas as pd
from typing import Dict


def compute_fairness_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    간호사별 야간/주말/총 근무/평균 위험도 요약 테이블.
    """
    work = df[df["shift_type"] != "OFF"].copy()

    grouped = work.groupby(["nurse_id", "nurse_name"])
    summary = grouped.agg(
        total_shifts=("date", "count"),
        night_shifts=("shift_type", lambda s: (s == "NIGHT").sum()),
        weekend_shifts=("weekend_flag", lambda s: s.sum()),
        mean_overall_risk=("overall_risk_score", "mean"),
    ).reset_index()

    summary["night_ratio"] = summary["night_shifts"] / summary["total_shifts"]
    summary["weekend_ratio"] = summary["weekend_shifts"] / summary["total_shifts"]

    return summary


def compute_fairness_stats(summary: pd.DataFrame) -> Dict[str, float]:
    """
    병동 전체 공정성 지표(분산, 표준편차 등)를 계산.
    """
    stats = {}
    if summary.empty:
        return stats

    stats["night_std"] = float(summary["night_shifts"].std(ddof=0))
    stats["weekend_std"] = float(summary["weekend_shifts"].std(ddof=0))
    stats["night_ratio_std"] = float(summary["night_ratio"].std(ddof=0))
    stats["weekend_ratio_std"] = float(summary["weekend_ratio"].std(ddof=0))
    stats["avg_mean_overall_risk"] = float(summary["mean_overall_risk"].mean())

    return stats


def generate_fairness_narrative(
    summary: pd.DataFrame, nurse_name: str
) -> str:
    """
    특정 간호사에 대한 공정성 해석 텍스트 생성.
    """
    if summary.empty:
        return "공정성 분석에 사용할 데이터가 없습니다."

    row = summary[summary["nurse_name"] == nurse_name]
    if row.empty:
        return f"{nurse_name}님에 대한 공정성 데이터가 없습니다."

    row = row.iloc[0]
    night_mean = summary["night_shifts"].mean()
    weekend_mean = summary["weekend_shifts"].mean()

    txt = []
    txt.append(
        f"{nurse_name}님의 전체 분석기간 기준 근무 요약입니다."
    )
    txt.append(
        f"- 총 근무일수(OFF 제외): {int(row['total_shifts'])}일"
    )
    txt.append(
        f"- 야간 근무: {int(row['night_shifts'])}회 "
        f"(병동 평균 {night_mean:.1f}회 대비 "
        f"{row['night_shifts'] - night_mean:+.1f}회 차이)"
    )
    txt.append(
        f"- 주말 근무: {int(row['weekend_shifts'])}회 "
        f"(병동 평균 {weekend_mean:.1f}회 대비 "
        f"{row['weekend_shifts'] - weekend_mean:+.1f}회 차이)"
    )
    txt.append(
        f"- 평균 위험 점수(overall risk): {row['mean_overall_risk']:.2f}"
    )

    return "\n".join(txt)

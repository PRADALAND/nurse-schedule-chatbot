# pages/1_Chatbot.py

import streamlit as st
import pandas as pd

from utils.features import (
    get_date_range_from_keyword,
    filter_schedule,
    compute_longest_work_streak,
    compute_longest_night_streak,
    find_peak_risk_info,
    date_in_range,
)
from utils.risk import risk_level
from utils.fairness import compute_fairness_table, generate_fairness_narrative

from utils.file_store import upload_file
from utils.analysis_log import log_analysis
from utils.free_ai import analyze_csv_free, analyze_image_free


PRESET_QUESTIONS = {
    "이번 달 위험도 요약": "이번달 내 근무 위험도 요약해줘",
    "이번 달 야간/주말 횟수": "이번달 야간, 주말 근무 횟수 알려줘",
    "이번 달 최장 연속근무": "이번달 최대 연속 근무일수와 연속야간 알려줘",
    "이번 달 quick return": "이번달 quick return 패턴과 횟수 알려줘",
}


def summarize_safety(df_slice, nurse_name, start, end):
    if df_slice.empty:
        return f"{start}~{end} 스케줄이 없습니다."

    n_work = (df_slice["shift_type"] != "OFF").sum()
    n_night = (df_slice["shift_type"] == "NIGHT").sum()
    n_ed = df_slice["ED_quick_return"].sum()
    n_nq = df_slice["N_quick_return"].sum()

    avg_risk = df_slice["overall_risk_score"].mean()
    max_risk = df_slice["overall_risk_score"].max()
    level = risk_level(int(max_risk))

    nurse_id = df_slice.iloc[0]["nurse_id"]

    cw_len, cw_start, cw_end = compute_longest_work_streak(df_slice, nurse_id)
    cn_len, cn_start, cn_end = compute_longest_night_streak(df_slice, nurse_id)

    peak = find_peak_risk_info(df_slice, nurse_id)
    if peak:
        if date_in_range(peak["date"], cw_start, cw_end):
            peak_line = f"- 최고 위험일: **{peak['date']}** (연속근무 {cw_len}일 구간 내부)"
        else:
            peak_line = f"- 최고 위험일: **{peak['date']}**"
    else:
        peak_line = ""

       lines = [
        f"### {nurse_name}님의 {start}~{end} 위험요약",
        f"- 근무일수: **{n_work}일**, 야간 **{n_night}회**",
        f"- 평균 위험점수: **{avg_risk:.2f}**, 최고점수: **{max_risk:.0f}** ({level})",
        f"- 최장 연속근무: **{cw_len}일** ({cw_start}~{cw_end})" if cw_len > 1 else "- 연속근무 없음",
        f"- 최장 연속야간: **{cn_len}일** ({cn_start}~{cn_end})" if cn_len > 1 else "- 연속야간 없음",
        f"- Quick return: ED {n_ed}회, ND {n_nq}회",
        peak_line,
    ]

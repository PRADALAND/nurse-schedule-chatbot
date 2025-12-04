import pandas as pd
import datetime as dt
from typing import Tuple

REQUIRED_COLS = ["date", "nurse_id", "nurse_name", "shift_code"]

OFF_CODES = {"OFF", "O", "휴무", "OFFDAY"}
NIGHT_CODES = {"N", "NIGHT", "NS"}
EVENING_CODES = {"E", "EVENING"}
DAY_CODES = {"D", "DAY", "DS", "9D", "LEADER"}
IGNORED_CODES = {"A"}  # UM 등 분석 제외


def normalize_shift_code(code: str) -> str:
    if pd.isna(code):
        return ""
    s = str(code).strip().upper()
    if s == "8D":
        return "9D"
    return s


def classify_shift(code: str) -> str:
    if code in OFF_CODES:
        return "OFF"
    if code in NIGHT_CODES:
        return "NIGHT"
    if code in EVENING_CODES:
        return "EVENING"
    if code in DAY_CODES:
        return "DAY"
    return "OTHER"


def load_schedule_file(uploaded_file) -> pd.DataFrame:
    fname = uploaded_file.name.lower()
    if fname.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["shift_code"] = df["shift_code"].apply(normalize_shift_code)
    df = df[~df["shift_code"].isin(IGNORED_CODES)]

    if "is_novice" not in df.columns:
        df["is_novice"] = False

    return df


def _compute_consecutive_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["nurse_id", "date"])
    df["prev_date"] = df.groupby("nurse_id")["date"].shift(1)
    df["prev_shift_code"] = df.groupby("nurse_id")["shift_code"].shift(1)
    df["prev_shift_type"] = df.groupby("nurse_id")["shift_type"].shift(1)

    cw_map = {}
    cn_map = {}

    for nurse_id, group in df.groupby("nurse_id", sort=False):
        group = group.sort_values("date")
        cw = 0
        cn = 0
        last_date = None

        for idx, row in group.iterrows():
            if row["shift_type"] == "OFF":
                cw = 0
                cn = 0
            else:
                if last_date is not None and (row["date"] - last_date).days == 1:
                    cw += 1
                else:
                    cw = 1

                if row["shift_type"] == "NIGHT":
                    if last_date is not None and (row["date"] - last_date).days == 1 and row["prev_shift_type"] == "NIGHT":
                        cn += 1
                    else:
                        cn = 1
                else:
                    cn = 0

            cw_map[idx] = cw
            cn_map[idx] = cn
            last_date = row["date"]

    df["consecutive_working_days"] = df.index.map(cw_map).fillna(0).astype(int)
    df["consecutive_night_shifts"] = df.index.map(cn_map).fillna(0).astype(int)
    return df


def _compute_staffing_features(df: pd.DataFrame) -> pd.DataFrame:
    # 날짜-근무코드별 실제 인원
    staffed = (
        df[df["shift_type"] != "OFF"]
        .groupby(["date", "shift_code"])["nurse_id"]
        .nunique()
    )
    df["staffing_count"] = list(
        df.set_index(["date", "shift_code"]).index.map(
            lambda key: staffed.get(key, 0)
        )
    )

    # 기준 인원 (엑셀 정의 기반)
    def baseline_for_row(row) -> int:
        code = row["shift_code"]
        stype = row["shift_type"]
        if code == "9D":
            return 1
        if stype == "DAY":
            return 6
        if stype == "EVENING":
            return 6
        if stype == "NIGHT":
            return 5
        return 0

    df["staffing_baseline"] = df.apply(baseline_for_row, axis=1)
    df["staffing_diff"] = (df["staffing_baseline"] - df["staffing_count"]).astype(int)
    return df


def _compute_quick_return_flags(df: pd.DataFrame) -> pd.DataFrame:
    # ED_quick_return: E → D/9D (엑셀 기준)
    df["ED_quick_return"] = (
        (df["prev_shift_type"] == "EVENING")
        & (df["shift_type"] == "DAY")
        & (df["shift_code"].isin({"D", "9D"}))
    )

    # N_quick_return: N → D/9D/E (엑셀 기준)
    df["N_quick_return"] = (
        (df["prev_shift_type"] == "NIGHT")
        & (
            (df["shift_code"].isin({"D", "9D"}))
            | (df["shift_type"] == "EVENING")
        )
    )
    return df


def add_base_features(df: pd.DataFrame) -> pd.DataFrame:
    """shift_type, weekend, 연속근무, quick return, staffing 등 기본 피처 계산."""
    df = df.copy()
    df["shift_type"] = df["shift_code"].apply(classify_shift)
    df["weekday"] = df["date"].apply(lambda d: d.weekday())
    df["weekend_flag"] = df["weekday"].isin({5, 6})

    df = _compute_consecutive_features(df)
    df = _compute_staffing_features(df)
    df = _compute_quick_return_flags(df)
    return df


def get_date_range_from_keyword(keyword: str) -> Tuple[dt.date, dt.date]:
    text = keyword.replace(" ", "")
    today = dt.date.today()

    if "오늘" in text:
        return today, today
    if "내일" in text:
        d = today + dt.timedelta(days=1)
        return d, d
    if "이번주" in text:
        start = today - dt.timedelta(days=today.weekday())
        end = start + dt.timedelta(days=6)
        return start, end
    if "다음주" in text:
        start = today - dt.timedelta(days=today.weekday()) + dt.timedelta(days=7)
        end = start + dt.timedelta(days=6)
        return start, end
    if "이번달" in text or "이번월" in text:
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1) - dt.timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1) - dt.timedelta(days=1)
        return start, end

    return today, today


def filter_schedule(df: p_


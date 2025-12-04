import pandas as pd
import datetime as dt
from typing import Tuple

REQUIRED_COLS = ["date", "nurse_id", "nurse_name", "shift_code"]

OFF_CODES = {"OFF", "O", "휴무", "OFFDAY"}
NIGHT_CODES = {"N", "NIGHT", "NS"}
EVENING_CODES = {"E", "EVENING"}
DAY_CODES = {"D", "DAY", "DS", "9D", "LEADER"}  # 8D는 아래에서 9D로 매핑
IGNORED_CODES = {"A"}  # 유엠 등 분석 제외


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
    """CSV/XLSX 스케줄 파일 로딩 및 최소 전처리."""
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

    # is_novice 등 나머지 피처는 기본값으로 생성 (사용자가 향후 채우도록)
    if "is_novice" not in df.columns:
        df["is_novice"] = False

    return df


def add_base_features(df: pd.DataFrame) -> pd.DataFrame:
    """근무유형, 주말여부, 연속근무, 연속야간, 일별 인력 수 등 기본 피처를 계산한다."""
    df = df.copy()
    df["shift_type"] = df["shift_code"].apply(classify_shift)
    df["weekday"] = df["date"].apply(lambda d: d.weekday())
    df["weekend_flag"] = df["weekday"].isin({5, 6})

    # 간호사별로 날짜 기준 정렬 후 이전 근무 정보 추가
    df = df.sort_values(["nurse_id", "date"])
    df["prev_date"] = df.groupby("nurse_id")["date"].shift(1)
    df["prev_shift_code"] = df.groupby("nurse_id")["shift_code"].shift(1)
    df["prev_shift_type"] = df.groupby("nurse_id")["shift_type"].shift(1)

    # 연속 근무일수 / 연속 야간 계산
    consec_work = []
    consec_night = []

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

            last_date = row["date"]
            consec_work.append((idx, cw, cn))

    cw_series = pd.Series({idx: cw for idx, cw, _ in consec_work})
    cn_series = pd.Series({idx: cn for idx, _, cn in consec_work})

    df["consecutive_working_days"] = df.index.map(cw_series).fillna(0).astype(int)
    df["consecutive_night_shifts"] = df.index.map(cn_series).fillna(0).astype(int)

    # 일별 인력 수 (OFF 제외)
    staffing_per_date = (
        df[df["shift_type"] != "OFF"]
        .groupby("date")["nurse_id"]
        .nunique()
    )
    df["staffing_count"] = df["date"].map(staffing_per_date).fillna(0).astype(int)

    return df


def get_date_range_from_keyword(keyword: str) -> Tuple[dt.date, dt.date]:
    """'오늘', '내일', '이번주', '다음주', '이번달' 등 키워드를 날짜 범위로 변환."""
    text = keyword.replace(" ", "")
    today = dt.date.today()

    if "오늘" in text:
        return today, today
    if "내일" in text:
        d = today + dt.timedelta(days=1)
        return d, d

    # 이번 주 (월~일)
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

    # 기본값: 오늘
    return today, today


def filter_schedule(df: pd.DataFrame, nurse_name: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    mask = (
        (df["nurse_name"] == nurse_name)
        & (df["date"] >= start)
        & (df["date"] <= end)
    )
    return df.loc[mask].sort_values("date")

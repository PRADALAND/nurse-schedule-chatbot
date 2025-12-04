import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
from typing import Optional, Tuple

# ============================================================
# 상수 및 기본 설정
# ============================================================

st.set_page_config(page_title="간호사 스케줄 챗봇", layout="wide")

REQUIRED_COLS = ["date", "nurse_id", "nurse_name", "shift_code"]

# 근무코드 매핑 (예시)
OFF_CODES = {"OFF", "O", "휴무", "OFFDAY"}
NIGHT_CODES = {"N", "NIGHT", "NS"}
EVENING_CODES = {"E", "EVENING"}
DAY_CODES = {"D", "DAY", "DS", "9D", "LEADER"}  # 8D는 아래에서 9D로 매핑

IGNORED_CODES = {"A"}  # A: 유엠 등 스케줄 분석 대상에서 제외


# ============================================================
# 유틸 함수: 전처리 및 피처 생성
# ============================================================

def normalize_shift_code(s: str) -> str:
    """
    근무코드를 대문자로 정규화하고, 8D -> 9D 등 단순 매핑을 수행.
    """
    if pd.isna(s):
        return ""
    s = str(s).strip().upper()

    # 예: 8D는 9D로 통일
    if s == "8D":
        return "9D"
    return s


def load_schedule(uploaded_file) -> pd.DataFrame:
    """
    CSV 또는 XLSX 스케줄 파일을 읽어서 기본 형태의 DataFrame으로 반환.
    필수 컬럼: date, nurse_id, nurse_name, shift_code
    """
    if uploaded_file.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")

    # 날짜 변환
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # 근무코드 정규화
    df["shift_code"] = df["shift_code"].apply(normalize_shift_code)

    # 유엠(A) 등 분석대상 제외
    df = df[~df["shift_code"].isin(IGNORED_CODES)]

    return df


def classify_shift(code: str) -> str:
    """
    근무코드를 근무종류(DAY/EVE/NIGHT/OFF/OTHER)로 분류.
    """
    if code in OFF_CODES:
        return "OFF"
    if code in NIGHT_CODES:
        return "NIGHT"
    if code in EVENING_CODES:
        return "EVENING"
    if code in DAY_CODES:
        return "DAY"
    return "OTHER"


def compute_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    스케줄 전체에 대해 근무유형, 주말 여부 등 기본 피처를 추가.
    """
    df = df.copy()
    df["shift_type"] = df["shift_code"].apply(classify_shift)
    df["weekday"] = df["date"].apply(lambda d: d.weekday())  # 0=월, 6=일
    df["is_weekend"] = df["weekday"].isin({5, 6})  # 토/일
    return df


def get_date_range(keyword: str) -> Tuple[dt.date, dt.date]:
    """
    '오늘', '내일', '이번주', '다음주', '이번달' 등의 한국어 키워드를
    간단한 날짜 범위로 매핑.
    """
    today = dt.date.today()

    if "오늘" in keyword:
        return today, today
    if "내일" in keyword:
        return today + dt.timedelta(days=1), today + dt.timedelta(days=1)

    # 이번 주 (월요일~일요일)
    if "이번주" in keyword:
        start = today - dt.timedelta(days=today.weekday())
        end = start + dt.timedelta(days=6)
        return start, end

    # 다음 주
    if "다음주" in keyword:
        start = today - dt.timedelta(days=today.weekday()) + dt.timedelta(days=7)
        end = start + dt.timedelta(days=6)
        return start, end

    # 이번 달
    if "이번달" in keyword or "이번 달" in keyword:
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1) - dt.timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1) - dt.timedelta(days=1)
        return start, end

    # 기본: 오늘
    return today, today


def filter_schedule(
    df: pd.DataFrame, nurse_name: str, start: dt.date, end: dt.date
) -> pd.DataFrame:
    """
    특정 간호사 + 기간에 해당하는 스케줄 필터링.
    """
    mask = (
        (df["nurse_name"] == nurse_name)
        & (df["date"] >= start)
        & (df["date"] <= end)
    )
    return df[mask].sort_values("date")


def compute_fatigue_score(sub: pd.DataFrame) -> dict:
    """
    예시용 피로도/위험도 점수 계산.
    ※ 실제 연구나 서비스에 사용할 경우, 반드시 별도 근거·검증이 필요함.
    """
    if sub.empty:
        return {
            "n_night": 0,
            "n_evening": 0,
            "n_weekend_shifts": 0,
            "max_consec_nights": 0,
            "fatigue_score": 0,
        }

    sub = sub.sort_values("date")
    n_night = (sub["shift_type"] == "NIGHT").sum()
    n_evening = (sub["shift_type"] == "EVENING").sum()
    n_weekend = ((sub["shift_type"] != "OFF") & (sub["is_weekend"])).sum()

    # 연속 야간 수 계산
    consec = 0
    max_consec = 0
    prev_date = None
    for _, row in sub.iterrows():
        if row["shift_type"] == "NIGHT":
            if prev_date is not None and (row["date"] - prev_date).days == 1:
                consec += 1
            else:
                consec = 1
            max_consec = max(max_consec, consec)
        else:
            consec = 0
        prev_date = row["date"]

    # 예시 피로도 공식 (임의, 설명용)
    fatigue_score = n_night * 2 + n_evening * 1 + n_weekend * 1 + max_consec * 1

    return {
        "n_night": int(n_night),
        "n_evening": int(n_evening),
        "n_weekend_shifts": int(n_weekend),
        "max_consec_nights": int(max_consec),
        "fatigue_score": int(fatigue_score),
    }


# ============================================================
# 챗봇 응답 로직 (간단 패턴 기반)
# ============================================================

def generate_answer(
    user_msg: str,
    df: pd.DataFrame,
    default_nurse: Optional[str] = None,
) -> str:
    """
    간단한 한국어 패턴을 사용해 질의 해석 후 스케줄 기반 답변 생성.
    """
    if df is None or df.empty:
        return "먼저 스케줄 파일을 업로드해 주세요."

    msg = user_msg.strip()
    lower = msg.lower()

    # 사용할 간호사 이름 결정
    nurse_name = default_nurse
    # 메시지 안에 등장하는 간호사 이름이 있으면 그 이름으로 override
    possible_names = df["nurse_name"].dropna().unique().tolist()
    for name in possible_names:
        if isinstance(name, str) and name in msg:
            nurse_name = name
            break

    if not nurse_name:
        return "어느 간호사 스케줄을 볼지 이름을 선택하거나, 질문에 간호사 이름을 포함해 주세요."

    # 날짜 범위 해석
    start, end = get_date_range(msg)

    sub = filter_schedule(df, nurse_name, start, end)

    # 1) "오늘 근무 뭐야?", "내일 근무?" 유형
    if "근무" in msg and ("오늘" in msg or "내일" in msg):
        if sub.empty:
            return f"{nurse_name}님은 해당 일자에 스케줄이 없습니다."
        row = sub.iloc[0]
        return (
            f"{nurse_name}님의 {row['date']} 근무는 "
            f"코드 {row['shift_code']} ({row['shift_type']}) 입니다."
        )

    # 2) "이번주 야간 몇 번?", "이번달 야간 근무 개수" 등
    if ("야간" in msg or "night" in lower) and (
        "몇" in msg or "개" in msg or "횟수" in msg
    ):
        if sub.empty:
            return f"{nurse_name}님의 해당 기간 스케줄이 없습니다."
        n_night = (sub["shift_type"] == "NIGHT").sum()
        return (
            f"{nurse_name}님의 {start} ~ {end} 기간 야간 근무 횟수는 "
            f"{int(n_night)}회입니다."
        )

    # 3) "이번주 전체 스케줄 보여줘" 유형
    if "전체" in msg or "스케줄" in msg or "표" in msg:
        if sub.empty:
            return f"{nurse_name}님의 {start} ~ {end} 기간 스케줄이 없습니다."
        # 간단 텍스트 요약
        lines = [
            f"{nurse_name}님의 {start} ~ {end} 스케줄 요약입니다:",
        ]
        for _, row in sub.iterrows():
            lines.append(
                f"- {row['date']} : {row['shift_code']} ({row['shift_type']})"
            )
        return "\n".join(lines)

    # 4) "피로도", "위험도" 등 질문 → 예시 점수 설명
    if ("피로도" in msg) or ("위험도" in msg):
        if sub.empty:
            return f"{nurse_name}님의 {start} ~ {end} 기간 스케줄이 없습니다."
        feat = compute_fatigue_score(sub)
        return (
            f"{nurse_name}님의 {start} ~ {end} 기간 예시 피로도/위험도 요약입니다.\n"
            f"- 야간 근무 횟수: {feat['n_night']}회\n"
            f"- 이브닝 근무 횟수: {feat['n_evening']}회\n"
            f"- 주말 근무(OFF 제외) 횟수: {feat['n_weekend_shifts']}회\n"
            f"- 최대 연속 야간 근무일수: {feat['max_consec_nights']}일\n"
            f"- 예시 피로도 점수(임의): {feat['fatigue_score']}점\n\n"
            f"※ 이 점수는 설명을 위한 임의 예시이며, 실제 임상/연구에서 사용하려면 "
            f"명확한 정의와 검증이 필요합니다."
        )

    # 기본 응답: 해당 기간 스케줄 간단 요약 + 피로도 간단 요약
    if sub.empty:
        return (
            f"질문의 의미를 정확히 해석하기 어려워 기본 스케줄만 확인했는데,\n"
            f"{nurse_name}님의 {start} ~ {end} 기간 스케줄이 없습니다."
        )

    feat = compute_fatigue_score(sub)
    n_shifts = (sub["shift_type"] != "OFF").sum()

    return (
        f"질문을 바탕으로 {nurse_name}님의 {start} ~ {end} 기간 스케줄을 요약했습니다.\n"
        f"- 총 근무일수(OFF 제외): {int(n_shifts)}일\n"
        f"- 야간 근무: {feat['n_night']}회, 이브닝: {feat['n_evening']}회\n"
        f"- 최대 연속 야간: {feat['max_consec_nights']}일\n"
        f"- 예시 피로도 점수(임의): {feat['fatigue_score']}점\n\n"
        f"보다 구체적인 질문(예: '이번주 내 야간 몇 번이야?', "
        f"'오늘 내 근무 뭐야?')을 하시면 더 정확하게 답변할 수 있습니다."
    )


# ============================================================
# Streamlit UI
# ============================================================

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "schedule_df" not in st.session_state:
        st.session_state["schedule_df"] = None
    if "default_nurse" not in st.session_state:
        st.session_state["default_nurse"] = None


def main():
    init_session_state()

    st.title("간호사 스케줄 챗봇 (Streamlit)")

    with st.sidebar:
        st.header("1. 스케줄 파일 업로드")
        uploaded = st.file_uploader(
            "CSV 또는 XLSX 업로드 (필수 컬럼: date, nurse_id, nurse_name, shift_code)",
            type=["csv", "xlsx"],
        )

        if uploaded is not None:
            try:
                df = load_schedule(uploaded)
                df = compute_basic_features(df)
                st.session_state["schedule_df"] = df

                st.success(f"스케줄 로딩 완료. 총 {len(df)}행.")
                st.dataframe(df.head(20))
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

        # 기본 간호사 선택
        df = st.session_state.get("schedule_df")
        if df is not None:
            nurse_list = sorted(df["nurse_name"].dropna().unique().tolist())
            default_nurse = st.selectbox(
                "기본 간호사(내 스케줄 기준)를 선택하세요.",
                options=["(선택 안 함)"] + nurse_list,
            )
            if default_nurse != "(선택 안 함)":
                st.session_state["default_nurse"] = default_nurse
        else:
            st.info("스케줄 파일을 먼저 업로드해 주세요.")

    st.header("2. 스케줄 기반 챗봇")

    # 기존 대화 출력
    for msg in st.session_state["messages"]:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)
        else:
            with st.chat_message("assistant"):
                st.markdown(content)

    # 새 질문 입력
    user_input = st.chat_input("스케줄 관련해서 무엇이든 물어보세요. (예: '나 오늘 근무 뭐야?')")
    if user_input:
        # 사용자 메시지 저장
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 답변 생성
        df = st.session_state.get("schedule_df")
        default_nurse = st.session_state.get("default_nurse")
        answer = generate_answer(user_input, df, default_nurse)

        st.session_state["messages"].append({"role": "assistant", "content": answer})

        with st.chat_message("assistant"):
            st.markdown(answer)


if __name__ == "__main__":
    main()

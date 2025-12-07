import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# =========================================================
# 0. Hugging Face Router 설정
# =========================================================
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"


# =========================================================
# 1. LLM 호출 함수 (Router ChatCompletion)
# =========================================================
def call_llm(system_prompt: str, user_prompt: str) -> str:
    if not HF_API_TOKEN:
        return "❌ HF_API_TOKEN이 설정되지 않았습니다."

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": HF_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 500,
        "temperature": 0.2,
    }

    resp = requests.post(HF_API_URL, headers=headers, json=payload)

    if resp.status_code != 200:
        return f"❌ LLM API 오류 (status {resp.status_code}): {resp.text}"

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return f"❌ LLM 응답 파싱 오류: {data}"


# =========================================================
# 2. 근무코드 정규화 / 타입 매핑
#    (근무표_코딩.xlsx 코드북 기준 단순화)
# =========================================================
def normalize_shift_code(raw):
    if pd.isna(raw):
        return "OFF"
    s = str(raw).strip().upper()

    # 코드북 기준 매핑
    mapping = {
        "DL": "D",
        "9D": "9D",
        "교외": "D",
        "A": "D",
        "검진": "D",
        "보예": "D",
        "EL": "E",
        "NL": "N",
        "유급": "OFF",
    }
    s = mapping.get(s, s)

    # 존재하지 않는 코드들은 일단 "기타 근무일"로 취급하지 않고 그대로 두되,
    # OFF, D/E/N 계열만 확실히 분류
    if s in {"D", "9D"}:
        return s
    if s in {"E"}:
        return s
    if s in {"N"}:
        return s
    if s in {"OFF"}:
        return "OFF"
    return s  # 특수 코드가 있으면 그대로 유지


def shift_to_token(norm):
    """
    ED_quick_return / N_quick_return 패턴 분석용 추상 토큰
    D/9D → 'D', E → 'E', N → 'N', OFF/유급 → 'O'
    그 외 근무일은 일단 'D'로 처리 (근무일로 보는 것이 안전)
    """
    if norm in {"D", "9D"}:
        return "D"
    if norm == "E":
        return "E"
    if norm == "N":
        return "N"
    if norm == "OFF":
        return "O"
    # 기타 근무코드는 'D'로 취급 (근무일)
    return "D"


# =========================================================
# 3. 한 간호사 기준 feature 계산 함수들
#    (코드북 규칙 반영)
# =========================================================
def compute_quick_returns(tokens):
    """
    tokens: 날짜 순으로 ['D','E','N','O', ...] 리스트
    코드북:
      ED_quick_return
        - Critical: ED, E9D → 여기서는 'ED'
        - Moderate: EOD, EO9D → 'EOD'
      N_quick_return
        - Critical: ND, N9D, NE, NOD, NO9D → 'ND','NE','NOD'
        - Moderate: NOE
    """

    ed_crit = ed_mod = 0
    n_crit = n_mod = 0
    n = len(tokens)

    for i in range(n - 1):
        a, b = tokens[i], tokens[i + 1]

        # E → D/9D (여기서는 모두 'D'로 통합)
        if a == "E" and b == "D":
            ed_crit += 1

        # N → D/E (N 다음 날 곧바로)
        if a == "N" and b in {"D", "E"}:
            n_crit += 1

    for i in range(n - 2):
        a, b, c = tokens[i], tokens[i + 1], tokens[i + 2]

        # E O D 패턴
        if a == "E" and b == "O" and c == "D":
            ed_mod += 1

        # N O D 패턴
        if a == "N" and b == "O" and c == "D":
            n_crit += 1

        # N O E 패턴
        if a == "N" and b == "O" and c == "E":
            n_mod += 1

    # Risk level (코드북: 존재 여부만으로 판정)
    def risk_from_counts(crit, mod):
        if crit > 0:
            return "Critical"
        if mod > 0:
            return "Moderate"
        return "No Risk"

    ed_risk = risk_from_counts(ed_crit, ed_mod)
    n_risk = risk_from_counts(n_crit, n_mod)

    return {
        "ED_quick_return_count_critical": ed_crit,
        "ED_quick_return_count_moderate": ed_mod,
        "ED_quick_return_risk": ed_risk,
        "N_quick_return_count_critical": n_crit,
        "N_quick_return_count_moderate": n_mod,
        "N_quick_return_risk": n_risk,
    }


def compute_consecutive_working_days(norm_codes):
    """
    consecutive_working_days (코드북):
      Critical: 6
      Moderate: 5
      Low: 4
      No: 3 이하
    OFF가 아닌 날을 '근무'로 본다.
    """
    max_streak = 0
    cur = 0
    for c in norm_codes:
        if c == "OFF":
            cur = 0
        else:
            cur += 1
            max_streak = max(max_streak, cur)

    if max_streak >= 6:
        risk = "Critical"
    elif max_streak == 5:
        risk = "Moderate"
    elif max_streak == 4:
        risk = "Low"
    else:
        risk = "No Risk"

    return max_streak, risk


def compute_consecutive_night_shifts(norm_codes):
    """
    consecutive_night_shifts (코드북):
      Critical: 5
      Moderate: 4
      Low: 3
      No: 2 이하
    """
    max_n_streak = 0
    cur = 0
    for c in norm_codes:
        if c == "N":
            cur += 1
            max_n_streak = max(max_n_streak, cur)
        else:
            cur = 0

    if max_n_streak >= 5:
        risk = "Critical"
    elif max_n_streak == 4:
        risk = "Moderate"
    elif max_n_streak == 3:
        risk = "Low"
    else:
        risk = "No Risk"

    return max_n_streak, risk


def compute_total_off_days(norm_codes):
    """
    total_off_days (코드북):
      Critical: ≤ 8
      Moderate: 9
      Low: 10,11
      No: ≥ 12
    """
    off_count = sum(1 for c in norm_codes if c == "OFF")

    if off_count <= 8:
        risk = "Critical"
    elif off_count == 9:
        risk = "Moderate"
    elif off_count in {10, 11}:
        risk = "Low"
    else:  # ≥ 12
        risk = "No Risk"

    return off_count, risk


def compute_total_night_days(norm_codes):
    """
    total_night_days (코드북):
      Critical: ≥ 7
      Moderate: -
      Low: 6
      No: ≤ 5
    """
    night_count = sum(1 for c in norm_codes if c == "N")

    if night_count >= 7:
        risk = "Critical"
    elif night_count == 6:
        risk = "Low"
    else:  # ≤ 5
        risk = "No Risk"

    return night_count, risk


def compute_min_off_interval(dates, norm_codes):
    """
    min_off_interval (코드북):
      Critical: Rest < 11
      Low: 11 ≤ Rest < 16
      No: Rest ≥ 16

    간단한 근무시간 가정:
      D/9D: 07:00–15:00 / 09:00–17:00
      E: 14:00–22:00
      N: 21:30–익일 07:30
      OFF: 근무 없음
    """
    # 날짜 순 정렬
    tmp = pd.DataFrame({"date": dates, "code": norm_codes}).sort_values("date")
    tmp["date"] = pd.to_datetime(tmp["date"])

    def shift_start_end(d, c):
        if c == "D":
            return d.replace(hour=7, minute=0), d.replace(hour=15, minute=0)
        if c == "9D":
            return d.replace(hour=9, minute=0), d.replace(hour=17, minute=0)
        if c == "E":
            return d.replace(hour=14, minute=0), d.replace(hour=22, minute=0)
        if c == "N":
            start = d.replace(hour=21, minute=30)
            end = (d + timedelta(days=1)).replace(hour=7, minute=30)
            return start, end
        return None, None  # OFF 또는 기타

    # 근무 있는 날만 추출
    work_days = []
    for _, row in tmp.iterrows():
        s, e = shift_start_end(row["date"], row["code"])
        if s is not None:
            work_days.append((s, e))

    if len(work_days) <= 1:
        # 근무가 거의 없으면 휴식은 충분하다고 가정
        return None, "No Risk"

    min_rest = None
    for i in range(len(work_days) - 1):
        end_i = work_days[i][1]
        start_j = work_days[i + 1][0]
        rest_hours = (start_j - end_i).total_seconds() / 3600.0
        if min_rest is None or rest_hours < min_rest:
            min_rest = rest_hours

    if min_rest is None:
        return None, "No Risk"

    if min_rest < 11:
        risk = "Critical"
    elif 11 <= min_rest < 16:
        risk = "Low"
    else:
        risk = "No Risk"

    return round(min_rest, 1), risk


# =========================================================
# 4. 전체 간호사별 Feature + Risk 요약
# =========================================================
def analyze_schedule(df):
    """
    df: columns = [date, nurse_id, nurse_name, shift_code, (level)]
    """
    required = {"date", "nurse_id", "nurse_name", "shift_code"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"필수 컬럼 누락: {missing}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["shift_norm"] = df["shift_code"].apply(normalize_shift_code)
    df["token"] = df["shift_norm"].apply(shift_to_token)

    results = []

    for nurse_id, g in df.groupby("nurse_id"):
        g = g.sort_values("date")
        nurse_name = g["nurse_name"].iloc[0]

        dates = list(g["date"])
        norm_codes = list(g["shift_norm"])
        tokens = list(g["token"])

        # 1) quick return
        qr = compute_quick_returns(tokens)

        # 2) 연속 근무 / 연속 야간
        max_cwd, cwd_risk = compute_consecutive_working_days(norm_codes)
        max_cns, cns_risk = compute_consecutive_night_shifts(norm_codes)

        # 3) OFF / Night 개수
        off_cnt, off_risk = compute_total_off_days(norm_codes)
        n_cnt, n_risk = compute_total_night_days(norm_codes)

        # 4) 최소 휴식시간
        min_rest, rest_risk = compute_min_off_interval(dates, norm_codes)

        # 5) 간단한 total 위험 점수 (Critical=3, Moderate=2, Low=1, No=0)
        def risk_score(label):
            if label == "Critical":
                return 3
            if label == "Moderate":
                return 2
            if label == "Low":
                return 1
            return 0

        total_score = (
            risk_score(qr["ED_quick_return_risk"])
            + risk_score(qr["N_quick_return_risk"])
            + risk_score(cwd_risk)
            + risk_score(cns_risk)
            + risk_score(off_risk)
            + risk_score(n_risk)
            + risk_score(rest_risk)
        )

        results.append(
            {
                "nurse_id": nurse_id,
                "nurse_name": nurse_name,
                "ED_quick_return_risk": qr["ED_quick_return_risk"],
                "N_quick_return_risk": qr["N_quick_return_risk"],
                "max_consecutive_working_days": max_cwd,
                "consecutive_working_days_risk": cwd_risk,
                "max_consecutive_night_shifts": max_cns,
                "consecutive_night_shifts_risk": cns_risk,
                "total_off_days": off_cnt,
                "total_off_days_risk": off_risk,
                "total_night_days": n_cnt,
                "total_night_days_risk": n_risk,
                "min_off_interval_hours": min_rest,
                "min_off_interval_risk": rest_risk,
                "total_risk_score": total_score,
            }
        )

    summary = pd.DataFrame(results)
    summary = summary.sort_values("total_risk_score", ascending=False)

    return summary


# =========================================================
# 5. Streamlit UI
# =========================================================
def main():
    st.title("근무 스케줄 챗봇 (코드북 기반 위험도 분석 + AI 요약)")

    uploaded = st.file_uploader("스케줄 파일 업로드 (CSV 또는 XLSX)", type=["csv", "xlsx"])

    if uploaded is not None:
        # 파일 확장자에 따라 읽기
        if uploaded.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)

        st.session_state["raw_df"] = df
        st.write("업로드된 원본 데이터 미리보기")
        st.dataframe(df.head())

        # Python 분석
        try:
            summary = analyze_schedule(df)
            st.session_state["summary"] = summary

            st.subheader("간호사별 위험도 요약 (코드북 기준)")
            st.dataframe(summary)
        except Exception as e:
            st.error(f"스케줄 분석 중 오류: {e}")

    query = st.text_input("질문을 입력하세요 (예: 이번 달 최악의 근무를 가진 간호사는 누구임?)")

    if st.button("질문 보내기") and query.strip():
        if "summary" not in st.session_state:
            st.error("먼저 스케줄 파일을 업로드하고 분석해야 합니다.")
            return

        summary = st.session_state["summary"]

        # LLM에 넘길 분석 요약 텍스트
        analysis_text = summary.to_string(index=False)

        system_prompt = (
            "너는 병동 간호사 근무 스케줄 공정성 및 피로도 분석 전문가다. "
            "입력으로 주어지는 표는 각 간호사별로, 코드북(ED_quick_return, N_quick_return, "
            "연속 근무일 수, 연속 Night 수, 휴무 개수, Night 개수, 최소 휴식시간 등)에 따라 계산된 "
            "위험도와 total_risk_score를 정리한 것이다. "
            "반드시 이 표에 있는 정보만 사용해서 질문에 답하고, "
            "표에 없는 정보나 추측은 절대 하지 마라."
        )

        user_prompt = (
            f"아래는 간호사별 근무 위험도 요약이다 (코드북 기준):\n\n"
            f"{analysis_text}\n\n"
            f"사용자 질문: {query}\n\n"
            f"질문에 대해, 어떤 간호사가 상대적으로 가장 힘든/위험한 근무 패턴을 가지고 있는지, "
            f"그 이유를 표의 지표를 근거로 논리적으로 설명해줘. "
            f"단, 근무표를 직접 보지 못하므로, 이 표에 나열된 수치와 위험도 등만 근거로 사용해야 한다."
        )

        with st.spinner("AI 응답 생성 중..."):
            answer = call_llm(system_prompt, user_prompt)

        st.subheader("AI 응답")
        st.markdown(answer)


if __name__ == "__main__":
    main()

# pages/1_Chatbot.py
import streamlit as st
import pandas as pd

from utils.features import (
    compute_longest_work_streak,
    compute_longest_night_streak,
    find_peak_risk_info,
)
from utils.risk import risk_level
from utils.analysis_log import log_analysis
from utils.free_ai import analyze_query_free


st.title("근무 스케줄 챗봇")

# ==========================
# 스케줄 데이터 확인
# ==========================
df = st.session_state.get("schedule_df", None)

if df is None:
    st.warning("스케줄 데이터가 없습니다. 메인 페이지에서 스케줄 파일을 업로드하세요.")
    st.stop()

# date 컬럼이 datetime이 아니면 변환
if not pd.api.types.is_datetime64_any_dtype(df["date"]):
    df["date"] = pd.to_datetime(df["date"])

# ==========================
# 사용자 입력
# ==========================
st.subheader("자연어로 질문해 보세요")
query = st.text_input(
    "질문을 입력하세요:",
    placeholder="예: 이번달 내 야간 근무랑 위험도 요약해줘",
)

if st.button("분석 요청"):
    if not query.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    # ------------------------------
    # 1) AI/규칙 기반으로 질의 해석
    # ------------------------------
    parsed = analyze_query_free(query, df)
    target_nurse = parsed.get("nurse_name")
    start_s = parsed.get("start_date")
    end_s = parsed.get("end_date")
    qtype = parsed.get("question_type", "summary")

    try:
        start = pd.to_datetime(start_s).date()
        end = pd.to_datetime(end_s).date()
    except Exception:
        start = df["date"].min().date()
        end = df["date"].max().date()

    # ------------------------------
    # 2) 스케줄 필터링
    # ------------------------------
    mask = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
    df_slice = df[mask].copy()

    if target_nurse is not None and "nurse_name" in df_slice.columns:
        df_slice = df_slice[df_slice["nurse_name"] == target_nurse]

    if df_slice.empty:
        response = f"{start}~{end} 구간에 해당하는 스케줄이 없습니다."
        st.write(response)
        log_analysis(query, response, meta={"parsed": parsed})
        st.stop()

    # ------------------------------
    # 3) 기본 요약 계산
    # ------------------------------
    n_work = (df_slice["shift_type"] != "OFF").sum()
    n_night = (df_slice["shift_type"] == "NIGHT").sum()

    # 연속 근무, 연속 야간, 피크 위험도 등도 있으면 계산
    longest_work = compute_longest_work_streak(df_slice)
    longest_night = compute_longest_night_streak(df_slice)
    peak_info = find_peak_risk_info(df_slice)  # 예: (날짜, 위험도 점수)

    # ------------------------------
    # 4) 한국어 자연어 응답 생성 (LLM 유무와 무관하게 여기서는 포맷팅)
    # ------------------------------
    subject = target_nurse if target_nurse else "전체 간호사"

    response_lines = []
    response_lines.append(
        f"📅 분석 기간: {start} ~ {end}"
    )
    response_lines.append(
        f"👤 대상: {subject}"
    )
    response_lines.append(
        f"• 근무일수: {int(n_work)}일 (OFF 제외)"
    )
    response_lines.append(
        f"• 야간 근무: {int(n_night)}회"
    )
    if longest_work is not None:
        response_lines.append(
            f"• 최장 연속 근무: {longest_work}일"
        )
    if longest_night is not None:
        response_lines.append(
            f"• 최장 연속 야간: {longest_night}일"
        )
    if peak_info is not None:
        peak_date, peak_score = peak_info
        level = risk_level(peak_score)
        response_lines.append(
            f"• 최고 위험도 날짜: {peak_date} (점수 {peak_score:.2f}, 등급 {level})"
        )

    response_lines.append("")
    response_lines.append("요약하면, 지정된 기간 동안의 전체 근무 패턴과 야간 편중, "
                          "위험도가 가장 높았던 시점을 함께 고려하여 스케줄 부담을 파악할 수 있습니다.")

    response = "\n".join(response_lines)

    # 화면 출력
    st.markdown(response.replace("\n", "  \n"))

    # ------------------------------
    # 5) 로그 저장
    # ------------------------------
    meta = {
        "parsed": parsed,
        "n_rows": int(len(df_slice)),
    }
    log_analysis(query, response, meta=meta)

import streamlit as st
import pandas as pd

from utils.features import get_date_range_from_keyword
from utils.analysis_log import log_analysis
from utils.free_ai import call_llm

st.title("근무 스케줄 챗봇 (AI 기반)")

df = st.session_state.get("schedule_df", None)

if df is None:
    st.warning("스케줄 데이터가 없습니다. 메인 페이지에서 파일 업로드하세요.")
    st.stop()

query = st.text_input(
    "질문을 입력하세요:",
    placeholder="예: '홍길동 이번달 야간 몇 번?', '이번달 위험도 요약', '누가 제일 힘들었어?'"
)

if st.button("분석 요청"):
    if not query.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    # ------------------------------
    # 날짜 범위 해석
    # ------------------------------
    start, end = get_date_range_from_keyword(query)
    df_slice = df[(df["date"] >= start) & (df["date"] <= end)]

    if df_slice.empty:
        st.error("해당 기간에 데이터가 없습니다.")
        st.stop()

    # ------------------------------
    # 개인별 통계 계산
    # ------------------------------
    def calc_max_streak(shifts):
        seq = (shifts != "OFF").astype(int)
        if seq.sum() == 0:
            return 0
        return seq.groupby((seq == 0).cumsum()).sum().max()

    stats = df_slice.groupby("nurse_name").agg(
        work_days=("shift_type", lambda x: (x != "OFF").sum()),
        night_days=("shift_type", lambda x: (x == "NIGHT").sum()),
        max_streak=("shift_type", calc_max_streak),
    ).reset_index()

    stats_text = "\n".join(
        f"- {row.nurse_name}: 근무일수 {row.work_days}일, NIGHT {row.night_days}회, 최장연속근무 {row.max_streak}일"
        for _, row in stats.iterrows()
    )

    # ------------------------------
    # 범용 LLM 프롬프트
    # ------------------------------
    prompt = f"""
너는 한국 병동에서 사용하는 '근무 스케줄 분석 챗봇'이다.
사용자의 질문을 그대로 이해하고, 아래 데이터만을 근거로 정확한 한국어 답변을 제공하라.

[사용자 질문]
{query}

[분석 기간]
{start} ~ {end}

[간호사별 근무 통계]
{stats_text}

[지시사항]
1) 질문의 의도를 먼저 파악하라.  
   - 특정 사람 분석?  
   - 전체 요약?  
   - 비교/순위 요청?  
   - 패턴 설명?  
   - 위험도 또는 업무강도 해석?  
   무엇이든 질문에 맞는 형태로 분석하라.

2) 반드시 위 통계만 사용하고, 없는 데이터(휴게시간/초과근무 등)는 추측하지 마라.

3) 질문이 모호하면 가장 자연스러운 해석을 선택해 설명하라.

4) 답변은 한국어로, 간결하면서도 전문적으로 작성하라.

"""

    response = call_llm(prompt)
    st.write(response)

    log_analysis(query, response)

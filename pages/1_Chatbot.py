import streamlit as st
import pandas as pd

from utils.features import get_date_range_from_keyword
from utils.analysis_log import log_analysis
from utils.free_ai import call_llm


# ----------------------------------------
# Streamlit 페이지 설정
# ----------------------------------------
st.set_page_config(page_title="근무 스케줄 챗봇", layout="wide")

st.title("근무 스케줄 챗봇 (AI 기반)")


# ----------------------------------------
# 데이터 불러오기
# ----------------------------------------
df = st.session_state.get("schedule_df", None)

if df is None:
    st.warning("스케줄 데이터가 없습니다. 메인 페이지에서 파일 업로드하세요.")
    st.stop()


# ----------------------------------------
# 대화 히스토리 구성
# ----------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def add_chat(role, message):
    st.session_state.chat_history.append({"role": role, "message": message})


# ----------------------------------------
# 개인별 통계 계산 함수
# ----------------------------------------
def calc_max_streak(shifts):
    seq = (shifts != "OFF").astype(int)
    if seq.sum() == 0:
        return 0
    return seq.groupby((seq == 0).cumsum()).sum().max()


# ----------------------------------------
# 대화 UI (좌측: 질문 입력 / 우측: 대화창)
# ----------------------------------------
col_input, col_chat = st.columns([1, 2])

with col_input:
    query = st.text_area(
        "질문을 입력하세요:",
        placeholder="예: '이번 달 가장 울고싶은 사람은?' 또는 '홍길동 야간 몇 번?'",
        height=200
    )

    if st.button("AI 분석 요청", use_container_width=True):
        if not query.strip():
            st.warning("질문을 입력하세요.")
            st.stop()

        # 날짜 범위 해석
        start, end = get_date_range_from_keyword(query)
        df_slice = df[(df["date"] >= start) & (df["date"] <= end)]

        # 개인별 통계 계산
        stats = df_slice.groupby("nurse_name").agg(
            work_days=("shift_type", lambda x: (x != "OFF").sum()),
            night_days=("shift_type", lambda x: (x == "NIGHT").sum()),
            max_streak=("shift_type", calc_max_streak),
        ).reset_index()

        stats_text = "\n".join(
            f"- {row.nurse_name}: 근무일수 {row.work_days}일, NIGHT {row.night_days}회, 최장연속근무 {row.max_streak}일"
            for _, row in stats.iterrows()
        )

        # LLM 프롬프트
        prompt = f"""
너는 한국 병동에서 쓰는 '근무 스케줄 분석 전문 AI'이다.

[사용자 질문]
{query}

[분석 기간]
{start} ~ {end}

[간호사별 근무 통계]
{stats_text}

[지시사항]
1) 위 개인별 통계는 충분한 정보이며, 이를 기반으로 사용자의 질문에 정확히 대답하라.
2) '데이터가 부족하다'라는 문장은 절대로 사용하지 마라.
3) 상대적 비교가 필요한 경우 NIGHT > 연속근무일 > 전체 근무일수 순으로 중요도를 두고 판단하라.
4) 반드시 한국어로 자연스럽게 설명하라.
5) 필요 시 근무 강도를 정량적/정성적으로 요약하라.
        """

        # 모델 호출
        ai_answer = call_llm(prompt)

        # 히스토리에 저장
        add_chat("user", query)
        add_chat("assistant", ai_answer)

        # 로그 저장
        log_analysis(query, ai_answer)


with col_chat:
    st.subheader("대화 기록")

    chat_container = st.container()
    with chat_container:
        if len(st.session_state.chat_history) == 0:
            st.info("아직 대화 기록이 없습니다.")
        else:
            for chat in st.session_state.chat_history:
                if chat["role"] == "user":
                    st.markdown(f"**👤 사용자:** {chat['message']}")
                else:
                    st.markdown(f"**🤖 AI:** {chat['message']}")
                st.markdown("---")

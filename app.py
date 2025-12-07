import streamlit as st
import pandas as pd

from utils.features import load_schedule_file, add_base_features
from utils.risk import add_risk_scores
from utils.fairness import compute_fairness_table, compute_fairness_stats


st.set_page_config(
    page_title="간호사 스케줄 인텔리전스",
    layout="wide",
)

import streamlit as st

def load_secrets():
    st.session_state["HF_API_TOKEN"] = st.secrets.get("HF_API_TOKEN")
    st.session_state["HF_API_URL"] = st.secrets.get("HF_API_URL")
    st.session_state["HF_MODEL"] = st.secrets.get("HF_MODEL")

load_secrets()


# ======================================
# 세션 상태 초기화
# ======================================
def init_state():
    st.session_state.setdefault("schedule_df", None)
    st.session_state.setdefault("fairness_summary", None)
    st.session_state.setdefault("fairness_stats", None)
    st.session_state.setdefault("nurse_list", [])


# ======================================
# 메인 로직
# ======================================
def main():
    init_state()

    st.title("간호사 스케줄 인텔리전스 (Nurse Schedule Intelligence)")

    st.markdown(
        """
        이 앱은 근무표(스케줄 파일)를 업로드하면,

        - 야간/연속근무, quick return 등 **기본 근무 특성**을 자동으로 계산하고  
        - **환자안전에 영향을 미치는 인력수준과 근무 패턴의 위험도**를 산출하며  
        - **간호사 간 근무 공정성**을 분석하여  
        **대시보드 · 챗봇 · 월별/일별 리포트**로 보여줍니다.
        """
    )

    # --------------------------------------
    # 사이드바 파일 업로드
    # --------------------------------------
    with st.sidebar:
        st.header("1. 스케줄 파일 업로드")
        uploaded = st.file_uploader(
            "CSV 또는 XLSX 파일 (필수 컬럼: date, nurse_id, nurse_name, shift_code)",
            type=["csv", "xlsx"],
        )

        if uploaded is not None:
            try:
                raw = load_schedule_file(uploaded)
                base = add_base_features(raw)
                full = add_risk_scores(base)

                # 저장
                st.session_state["schedule_df"] = full
                st.session_state["nurse_list"] = sorted(full["nurse_name"].dropna().unique().tolist())

                # 공정성 계산
                summary = compute_fairness_table(full)
                stats = compute_fairness_stats(summary)
                st.session_state["fairness_summary"] = summary
                st.session_state["fairness_stats"] = stats

                st.success(f"스케줄 로딩 및 피처 생성 완료 (총 {len(full)}행).")

            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

    # --------------------------------------
    # 업로드 안 했을 때 메시지
    # --------------------------------------
    df = st.session_state.get("schedule_df")

    if df is None:
        st.info("좌측에서 스케줄 파일을 업로드하면 전체 기능이 활성화됩니다.")
        return

    # --------------------------------------
    # 업로드된 표 출력
    # --------------------------------------
    st.subheader("업로드된 스케줄 및 피처 (상위 50행 미리보기)")
    st.dataframe(df.head(50))

    # --------------------------------------
    # 공정성 요약 출력
    # --------------------------------------
    st.subheader("간단 공정성 요약")
    fairness_summary = st.session_state["fairness_summary"]
    fairness_stats = st.session_state["fairness_stats"]

    if fairness_summary is not None and len(fairness_summary) > 0:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**간호사별 요약 테이블**")
            st.dataframe(fairness_summary)

        with col2:
            st.markdown("**병동 전체 공정성 지표**")
            st.write(fairness_stats)

    else:
        st.info("공정성 요약을 계산할 수 있는 데이터가 부족합니다.")


# ======================================
# 진입점
# ======================================
if __name__ == "__main__":
    main()

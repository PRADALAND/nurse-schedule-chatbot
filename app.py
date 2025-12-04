import streamlit as st
import pandas as pd

from utils.features import load_schedule_file, add_base_features
from utils.risk import add_risk_scores
from utils.fairness import compute_fairness_table, compute_fairness_stats


st.set_page_config(
    page_title="간호사 스케줄 인텔리전스",
    layout="wide",
)


def init_state():
    if "schedule_df" not in st.session_state:
        st.session_state["schedule_df"] = None
    if "fairness_summary" not in st.session_state:
        st.session_state["fairness_summary"] = None
    if "fairness_stats" not in st.session_state:
        st.session_state["fairness_stats"] = None


def main():
    init_state()

    st.title("간호사 스케줄 인텔리전스 (Nurse Schedule Intelligence)")
    st.markdown(
        """
        이 앱은 스케줄 파일을 업로드하면  
        1) 기본 피처(야간/주말/연속근무 등)를 계산하고  
        2) 피로도 및 위험도 점수(overall risk)를 산출하며  
        3) 공정성 대시보드와 챗봇, 일별 리포트를 제공합니다.  
        """
    )

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

                st.session_state["schedule_df"] = full

                st.success(f"스케줄 로딩 및 피처 생성 완료 (총 {len(full)}행).")

                nurse_list = sorted(full["nurse_name"].dropna().unique().tolist())
                st.session_state["nurse_list"] = nurse_list

                summary = compute_fairness_table(full)
                stats = compute_fairness_stats(summary)
                st.session_state["fairness_summary"] = summary
                st.session_state["fairness_stats"] = stats

            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

    df = st.session_state.get("schedule_df")

    if df is None:
        st.info("좌측에서 스케줄 파일을 업로드하면 전체 기능이 활성화됩니다.")
        return

    st.subheader("업로드된 스케줄 및 피처 (상위 50행 미리보기)")
    st.dataframe(df.head(50))

    st.subheader("간단 공정성 요약")
    fairness_summary = st.session_state.get("fairness_summary")
    fairness_stats = st.session_state.get("fairness_stats")

    if fairness_summary is not None and not fairness_summary.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**간호사별 요약 테이블**")
            st.dataframe(fairness_summary)

        with col2:
            st.markdown("**병동 전체 공정성 지표 (예시)**")
            if fairness_stats:
                st.write(
                    {
                        "야간 근무 횟수 표준편차": fairness_stats.get("night_std", None),
                        "주말 근무 횟수 표준편차": fairness_stats.get("weekend_std", None),
                        "야간 비율 표준편차": fairness_stats.get("night_ratio_std", None),
                        "주말 비율 표준편차": fairness_stats.get("weekend_ratio_std", None),
                        "평균 overall risk": fairness_stats.get("avg_mean_overall_risk", None),
                    }
                )
            else:
                st.write("계산 가능한 공정성 통계가 없습니다.")
    else:
        st.info("공정성 요약을 계산할 수 있는 데이터가 부족합니다.")


if __name__ == "__main__":
    main()


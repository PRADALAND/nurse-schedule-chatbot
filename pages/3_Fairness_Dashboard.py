import streamlit as st
import pandas as pd
from utils.fairness import compute_fairness_table, compute_fairness_stats


def main():

    st.title("공정성(Fairness) 대시보드")

    df = st.session_state.get("schedule_df", None)

    # 스케줄 없음 → 종료
    if df is None or df.empty:
        st.info("먼저 스케줄 파일을 업로드해주세요.")
        return

    # 공정성 테이블 생성
    try:
        fair = compute_fairness_table(df)
    except Exception as e:
        st.error(f"공정성 분석 중 오류: {e}")
        return

    # 만약 fair가 None이거나 컬럼이 없으면 방어
    if fair is None or fair.empty:
        st.warning("공정성 데이터를 계산할 수 없습니다.")
        return

    required_cols = [
        "nurse_name",
        "fairness_score",
        "pref_match_ratio",
        "total_off_days",
        "total_night_days",
        "min_off_interval",
        "level_night_ratio",
        "level_workingdays_ratio",
    ]
    for col in required_cols:
        if col not in fair.columns:
            st.error(f"필요한 컬럼 '{col}' 이(가) 존재하지 않습니다.")
            return

    # 정렬 (에러 방어)
    try:
        fair_sorted = fair.sort_values("fairness_score").reset_index(drop=True)
    except Exception as e:
        st.error(f"공정성 정렬 중 오류: {e}")
        return

    st.subheader("1) 공정성 낮은 RN 순 정렬")
    st.dataframe(fair_sorted[["nurse_name", "fairness_score"]])

    # RN 선택
    selected = st.selectbox(
        "공정성 상세 분석할 간호사를 선택하세요",
        fair_sorted["nurse_name"]
    )

    row = fair_sorted[fair_sorted["nurse_name"] == selected].iloc[0]

    # RN 세부 분석
    st.subheader("2) 선호 반영율")
    st.markdown(f"- **선호 근무 반영율:** {row['pref_match_ratio']:.1%}")

    st.subheader("3) OFF / Night / Interval")
    st.markdown(
        f"- 총 OFF 일수: **{int(row['total_off_days'])}일**\n"
        f"- 총 Night 일수: **{int(row['total_night_days'])}일**\n"
        f"- 최소 OFF 간격: **{int(row['min_off_interval'])}일**"
    )

    st.subheader("4) 연차 대비 공정성")
    st.markdown(
        f"- Night 비율(연차 보정): **{row['level_night_ratio']:.2f}**\n"
        f"- 근무일수 비율(연차 보정): **{row['level_workingdays_ratio']:.2f}**"
    )

    # 전체 통계
    st.subheader("5) 병동 전체 공정성 요약")
    stats = compute_fairness_stats(fair)
    st.write(stats)


if __name__ == "__main__":
    main()

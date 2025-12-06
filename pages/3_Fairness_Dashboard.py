import streamlit as st
import pandas as pd
from utils.fairness import compute_fairness_table, compute_fairness_stats

def main():
    st.title("공정성 대시보드 (Fairness Dashboard)")

    df = st.session_state.get("schedule_df")

    if df is None:
        st.warning("스케줄 파일을 먼저 업로드해주세요.")
        return

    st.markdown("""
    ### 이 대시보드는 다음을 분석합니다:
    - 부서 RN 간 근무 배분의 형평성
    - OFF / Night / Interval 기반 편중 여부
    - RN 개인별 공정성 지표
    """)

    # -------------------------------
    # 1. 공정성 테이블 계산
    # -------------------------------
    try:
        fair = compute_fairness_table(df)
    except Exception as e:
        st.error(f"공정성 계산 중 오류: {e}")
        return

    if fair.empty:
        st.warning("공정성 분석 지표가 비어 있습니다.")
        return

    # -------------------------------
    # 2. 병동 전체 공정성 통계
    # -------------------------------
    stats = compute_fairness_stats(fair)

    st.subheader("1) 병동 전체 공정성 요약 지표")

    colA, colB, colC, colD = st.columns(4)
    colA.metric("Fairness Score STD", f"{stats['fairness_score_std']:.3f}")
    colB.metric("평균 선호 반영율", f"{stats['avg_pref_match_ratio']:.2f}")
    colC.metric("Night 횟수 STD", f"{stats['total_night_std']:.2f}")
    colD.metric("OFF 일수 STD", f"{stats['total_off_std']:.2f}")

    st.caption("""
    STD(표준편차)가 높을수록 간호사 간 근무 분배 편차가 크다는 의미입니다.
    """)

    # -------------------------------
    # 3. RN 공정성 순위 리스트
    # -------------------------------
    st.subheader("2) RN 공정성 순위")

    fair_sorted = fair.sort_values("fairness_score").reset_index(drop=True)

    st.dataframe(
        fair_sorted[["nurse_name", "fairness_score"]],
        use_container_width=True,
    )

    selected = st.selectbox("상세 분석할 RN 선택", fair_sorted["nurse_name"])
    row = fair_sorted[fair_sorted["nurse_name"] == selected].iloc[0]

    # -------------------------------
    # 4. RN 상세 분석
    # -------------------------------
    st.subheader(f"3) {selected} 공정성 상세 분석")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Fairness Score", f"{row['fairness_score']:.3f}")
        st.metric("선호 반영율", f"{row['pref_match_ratio']:.2f}")
        st.metric("총 OFF 일수", int(row["total_off_days"]))

    with col2:
        st.metric("Night 근무 일수", int(row["total_night_days"]))
        st.metric("최소 OFF 간격", int(row["min_off_interval"]))
        st.metric("연차 대비 Night 비율", f"{row['level_night_ratio']:.2f}")

    # -------------------------------
    # 5. RN 텍스트 요약
    # -------------------------------
    st.markdown("""
    ### RN 공정성 해석 요약
    """)

    interpretation = []

    # OFF 일수 기반 해석
    if row["total_off_days"] <= fair["total_off_days"].median() - 2:
        interpretation.append("- OFF 일수가 전체 대비 낮아 상대적으로 휴식 부족 가능성이 있습니다.")
    elif row["total_off_days"] >= fair["total_off_days"].median() + 2:
        interpretation.append("- OFF 일수가 상대적으로 많아 배분 편차가 있을 수 있습니다.")
    else:
        interpretation.append("- OFF 일수는 병동 평균 범위 내에 있습니다.")

    # Night 기반
    if row["total_night_days"] >= fair["total_night_days"].median() + 1:
        interpretation.append("- Night 근무가 병동 평균보다 많은 편입니다.")
    else:
        interpretation.append("- Night 근무는 평균 범위입니다.")

    # OFF 간격
    if row["min_off_interval"] <= 1:
        interpretation.append("- OFF 간격이 매우 짧아 피로 누적 가능성이 있습니다.")
    else:
        interpretation.append("- OFF 간격은 무난한 수준입니다.")

    # 최종 해석 출력
    st.markdown("\n".join(interpretation))


if __name__ == "__main__":
    main()

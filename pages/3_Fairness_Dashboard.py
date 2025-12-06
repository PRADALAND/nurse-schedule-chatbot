import streamlit as st
from utils.fairness import compute_fairness_table, compute_fairness_stats

def main():
    st.title("공정성 대시보드 (Fairness Dashboard)")

    # ------------------------
    # 1) 데이터 존재 여부 체크
    # ------------------------
    df = st.session_state.get("schedule_df", None)

    if df is None or df.empty:
        st.info("스케줄 데이터가 없습니다. 먼저 Main 페이지에서 스케줄 파일을 업로드하세요.")
        return  # ★★★ 절대 fairness 계산을 진행하지 않음 ★★★

    # ------------------------
    # 2) 공정성 테이블 계산
    # ------------------------
    try:
        fair = compute_fairness_table(df)
    except Exception as e:
        st.error(f"공정성 테이블 생성 중 오류 발생: {e}")
        return

    # ------------------------
    # 3) 컬럼 검증: 없으면 바로 중단
    # ------------------------
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

    missing = [c for c in required_cols if c not in fair.columns]
    if missing:
        st.error(f"공정성 분석을 위해 필요한 컬럼이 없습니다: {missing}")
        st.dataframe(fair)  # 무엇이 들어있는지 보여줌 (디버그에 매우 중요)
        return  # ★★★ 여기서 안전하게 stop → 화면은 뜸 ★★★

    # ------------------------
    # 4) 공정성 테이블 정상 출력
    # ------------------------
    fair_sorted = fair.sort_values("fairness_score").reset_index(drop=True)

    st.subheader("간호사 공정성 순위 (낮을수록 불공정)")
    st.dataframe(fair_sorted)

    # ------------------------
    # 5) RN 선택해서 상세보기
    # ------------------------
    selected = st.selectbox("간호사 선택", fair_sorted["nurse_name"])
    row = fair_sorted[fair_sorted["nurse_name"] == selected].iloc[0]

    st.subheader("상세 공정성 분석")
    st.markdown(f"""
    - 공정성 점수: **{row['fairness_score']:.3f}**
    - 선호 패턴 반영률: **{row['pref_match_ratio']:.2f}**
    - OFF 일수: **{row['total_off_days']}**
    - 야간 근무 일수: **{row['total_night_days']}**
    - 최소 OFF 간격: **{row['min_off_interval']}일**
    - 연차 대비 야간 비율: **{row['level_night_ratio']:.2f}**
    - 연차 대비 근무일 비율: **{row['level_workingdays_ratio']:.2f}**
    """)

if __name__ == "__main__":
    main()

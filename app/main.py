# app/main.py
import streamlit as st
import repository as repo
import charts
import components

# 페이지 레이아웃 기본 설정
st.set_page_config(
    page_title="SH공사 모듈러 청년매입임대 최적지 발굴 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 제목 및 가이드라인 렌더링
st.title("🏗️ 서울시 동대문구 내 모듈러 기반 청년주택사업 최적 유망 행정동 발굴")
components.render_sidebar_guide()

# 저장소 계층을 통한 안전 데이터 로드
try:
    dates = repo.get_available_dates()
    if not dates:
        st.warning("데이터 마트에 가용할 수 있는 시계열 데이터가 존재하지 않습니다. 수집기를 점검하세요.")
        st.stop()
        
    # 상단 날짜 필터 (가장 최신 수집 데이터가 디폴트로 활성화)
    selected_date = st.selectbox("분석 기준 날짜 선택", dates)
    
    # 전체 마트 데이터 로드 후 선택 날짜 필터링
    df_all = repo.load_mart_data()
    df_filtered = df_all[df_all['base_date'] == selected_date].reset_index(drop=True)
    
    if df_filtered.empty:
        st.info("선택한 날짜에 해당하는 집계 데이터가 마트에 없습니다.")
        st.stop()
        
    # 종합 1위 행정동 raw 추출
    top_dong = df_filtered.iloc[0]
    
    # UI 컴포넌트 호출: 메인 KPI 스코어 카드 배치
    components.render_kpi_cards(top_dong)
    st.markdown("---")
    
    # 비즈니스 대시보드 화면 이원화 분리 레이아웃 (Tabs 활용)
    tab1, tab2 = st.tabs(["2차원 교차 검증 매트릭스", "종합 유망도 랭킹 차트"])
    
    with tab1:
        st.subheader("절대 규모(Volume)와 상대 밀도(Density)의 융합 분석")
        st.markdown(
            f"**의사결정 브리핑:** 현재 날짜({selected_date}) 기준, **{top_dong['dong_name']}**은 "
            f"동대문구 내 노후 주거, 협소 도로망, 규제를 만족하는 필지 위에 청년 절대 유입수와 상대 점유율 비율이 모두 균형 있게 조화된 **최고 후보지**로 증명됩니다."
        )
        # 산점도 차트 렌더링
        scatter_fig = charts.create_scatter_matrix(df_filtered)
        st.plotly_chart(scatter_fig, use_container_width=True)
        
    with tab2:
        col1, col2 = st.columns([0.6, 0.4])
        
        with col1:
            # 가로 막대 랭킹 차트 렌더링
            bar_fig = charts.create_priority_bar(df_filtered)
            st.plotly_chart(bar_fig, use_container_width=True)
            
        with col2:
            st.subheader("정밀 데이터 뷰")
            # 가독성을 높인 데이터프레임 노출
            st.dataframe(
                df_filtered[['dong_name', 'avg_youth_pop', 'youth_share_pct', 'final_volume_score', 'final_priority_score']],
                column_config={
                    "dong_name": "행정동명",
                    "avg_youth_pop": "청년 인구(명)",
                    "youth_share_pct": "청년 비율(%)",
                    "final_volume_score": "절대수요 점수",
                    "final_priority_score": "종합 점수"
                },
                use_container_width=True,
                hide_index=True
            )

except Exception as e:
    st.error(f"대시보드 연동 과정 중 치명적 예외 에러가 발생했습니다: {e}")

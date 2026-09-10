# app/main.py
import streamlit as st
import pandas as pd
import repository as repo
import charts
import components
import plotly.express as px

# 페이지 레이아웃 기본 설정
st.set_page_config(
    page_title="SH공사 모듈러 청년매입임대 최적지 발굴 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 제목 및 가이드라인 렌더링
st.title("🏗️ 서울시 동대문구 내 모듈러 기반 청년주택사업 최적 유망 행정동 발굴")
components.render_sidebar_guide()

try:
    df_all = repo.load_mart_data()
    dates = repo.get_available_dates()
    
    if df_all.empty:
        st.warning("데이터 마트에 데이터가 존재하지 않습니다. 수집기를 점검하세요.")
        st.stop()
        
    # 2개월치 전체 데이터 종합 (Aggregation)
    df_total = df_all.groupby(['dong_code', 'dong_name']).agg({
        'avg_youth_pop': 'mean',
        'youth_share_pct': 'mean',
        'final_volume_score': 'mean',
        'final_priority_score': 'mean'
    }).reset_index()
    
    # 종합 점수 높은 순 정렬
    df_total = df_total.sort_values(by="final_priority_score", ascending=False).reset_index(drop=True)
    
    # 종합 1위 행정동 추출
    top_dong = df_total.iloc[0]
    
    # 2개월 종합 메인 KPI 스코어 카드 배치
    components.render_kpi_cards(top_dong)
    st.markdown("---")
    
    # 비즈니스 대시보드 화면 이원화 분리 레이아웃 (Tabs 활용)
    tab1, tab2 = st.tabs(["2차원 교차 검증 매트릭스", "종합 유망도 랭킹 차트"])
    
    with tab1:
        st.subheader("절대 규모(Volume)와 상대 밀도(Density)의 융합 분석")
        st.markdown(
            f"**의사결정 브리핑:** 공공 API를 통한 수집기간 전체 기준, **{top_dong['dong_name']}**은 "
            f"동대문구 내 노후 주거, 협소 도로망, 규제를 만족하는 필지 위에 청년 절대 유입수와 상대 점유율 비율이 모두 균형 있게 조화된 **최고 후보지**로 증명됩니다."
        )
        
        # 2개월 종합 데이터를 바탕으로 산점도 렌더링
        scatter_fig = charts.create_scatter_matrix(df_total)
        st.plotly_chart(scatter_fig, use_container_width=True)
        
    with tab2:
        col1, col2 = st.columns([0.6, 0.4])
        
        with col1:
            # 2개월 종합 데이터를 바탕으로 가로 막대 랭킹 차트 렌더링
            bar_fig = charts.create_priority_bar(df_total)
            st.plotly_chart(bar_fig, use_container_width=True)
            
        with col2:
            st.subheader("정밀 데이터 뷰")
            st.dataframe(
                df_total[['dong_name', 'avg_youth_pop', 'youth_share_pct', 'final_volume_score', 'final_priority_score']],
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
            
        # ----------------------------------------------------
        # 하단 영역: 행정동별 시계열 트렌드 및 일별 세부 확인
        # ----------------------------------------------------
        st.markdown("---")
        st.subheader("행정동 일별 세부 추이 분석")
        st.write("분석하고 싶은 행정동을 선택하면, 전체 수집 기간 동안의 일별 종합스코어 추이와 세부 데이터를 확인할 수 있습니다.")
        
        selected_dong = st.selectbox("행정동 선택", df_total['dong_name'].unique(), key="dong_trend_selector")
        
        df_dong_trend = df_all[df_all['dong_name'] == selected_dong].copy()

        # base_date가 '20260903' 같은 문자열이나 숫자일 경우 그래프 선이 뭉개지는 것을 방지하기 위해 시계열 타입으로 변환
        df_dong_trend['base_date'] = pd.to_datetime(df_dong_trend['base_date'].astype(str), format='%Y%m%d', errors='coerce')
        # 혹시 위 포맷이 안 맞을 경우를 대비한 일반 변환 방어코드
        if df_dong_trend['base_date'].isna().all():
            df_dong_trend['base_date'] = pd.to_datetime(df_all[df_all['dong_name'] == selected_dong]['base_date'], errors='coerce')
            
        # 날짜 순서대로 정렬
        df_dong_trend = df_dong_trend.sort_values('base_date').reset_index(drop=True)
        
        # 3. 레이아웃 분할
        trend_col, table_col = st.columns(2)
        
        with trend_col:
            st.markdown(f"**종합 점수 추이**")
            
            fig_trend = px.line(
                df_dong_trend, 
                x='base_date', 
                y='final_priority_score',
                markers=True,
                labels={"base_date": "수집 일자", "final_priority_score": "종합 유망도 스코어"},
            )
            # X축 날짜 포맷
            fig_trend.update_xaxes(
                tickmode="linear",
                dtick=14 * 24 * 60 * 60 * 1000,  
                tickformat="%m/%d"   
            )

            fig_trend.update_yaxes(
                range=[0, 1000],          # 0점부터 1000점까지 축 고정
                dtick=200,                # 눈금선을 200점 단위
                nticks=6,
                showgrid=True,            
                gridcolor="rgba(200, 200, 200, 0.3)" 
            )

            st.plotly_chart(fig_trend, use_container_width=True)
            
        with table_col:
            st.markdown(f"**일자별 정밀 데이터 표**")
            
            # 테이블 가독성을 위해 날짜를 다시 'YYYY-MM-DD' 문자열로 변경
            df_table_show = df_dong_trend.copy()
            df_table_show['display_date'] = df_table_show['base_date'].dt.strftime('%Y-%m-%d')
            
            # 선택한 행정동의 일자별 수치들만 노출
            st.dataframe(
                df_table_show[['display_date', 'avg_youth_pop', 'youth_share_pct', 'final_priority_score']],
                column_config={
                    "display_date": "수집 일자",
                    "avg_youth_pop": "청년 인구(명)",
                    "youth_share_pct": "청년 비율(%)",
                    "final_priority_score": "종합 점수"
                },
                use_container_width=True,
                hide_index=True,
                height=400 
            )

except Exception as e:
    st.error(f"대시보드 연동 과정 중 치명적 예외 에러가 발생했습니다: {e}")

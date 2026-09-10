# app/components.py
import streamlit as st

def render_sidebar_guide():
    """대시보드 목적 안내 가이드 (2개월 종합 데이터 반영)"""
    with st.sidebar:
        st.header("SH공사 청년주택본부")
        st.subheader("도심형 매입임대 의사결정 가이드")
        st.markdown("---")
        st.markdown(
            """
            **의사결정 목표**
            * 동대문구 내 **자율주택정비사업 주택** 대상
            * 모듈러 공법 신속 신축 시 공실 위험이 제로(0)에 수렴하는 '청년 최적 매입임대주택 필지' 선정
            
            **교차 검증 지표 구조(2개월 종합)**
            1. **절대 수요 축 (Volume):** "청년 일평균 활동(생활)인구 규모"의 평균치 × 미니프로젝트1 최종유망 자치구 스코어링
            2. **상대 밀도 축 (Density):** "전체 생활 인구 중 2030 청년이 차지하는 비율(%)"의 평균치
            3. **원 크기 (Size):** "청년 일평균 활동(생활)인구 규모"의 평균치
            4. **색상 (Color):** 최종 종합 유망도 스코어링 평균 (절대 수요 × 상대 밀도)
            """
        )
        st.info("💡 우측 상단(1사면)에 위치한 행정동일수록 수집 기간 동안 절대 인구량과 청년 밀집도가 모두 높았던 안전 투자 요충지입니다.")

        st.markdown("---")
        st.markdown(
            """
            **데이터 출처 정보**
            \n서울 열린데이터광장(https://seoul.go.kr)
            \n서울시 행정동 단위 서울 생활인구(내국인) 공공 오픈 API
            """
        )

def render_kpi_cards(top_row):
    """최우선 공급 유망동 핵심 지표 요약 카드 배치 (2개월 종합 반영)"""
    st.markdown("### 최우선 공급 유망 행정동 제안")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="최우선 추천 동", 
            value=f"{top_row['dong_name']}",
            delta="청년 수요 최상위"
        )
    with col2:
        st.metric(
            label="청년 활동 인구", 
            value=f"{int(top_row['avg_youth_pop']):,} 명"
        )
    with col3:
        st.metric(
            label="청년 점유 비율", 
            value=f"{top_row['youth_share_pct']:.2f}%"
        )

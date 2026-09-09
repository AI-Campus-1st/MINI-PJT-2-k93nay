# app/repository.py
import pandas as pd
import sqlalchemy
import urllib.parse
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

def get_db_engine():
    """배포용 SQLite 파일(housing2.db)에 연결하는 엔진 생성"""
    # loader.py에서 생성한 데이터 파일과 똑같은 파일명을 지정합니다.
    db_url = "sqlite:///housing2.db"

    # 스트림릿 멀티스레드 환경에서 SQLite 충돌을 방지하는 필수 옵션 적용
    return sqlalchemy.create_engine(
        db_url, connect_args={"check_same_thread": False}
    )

@st.cache_data(ttl=600)
def load_mart_data():
    """최종 요약 마트 테이블에서 대시보드에 필요한 데이터 조회"""
    engine = get_db_engine()
    query = """
        SELECT 
            base_date,
            dong_code,
            dong_name,
            avg_youth_pop,
            ROUND(youth_occupancy_rate * 100, 2) AS youth_share_pct,
            final_volume_score,
            final_priority_score
        FROM mart_youth_housing_priority
        ORDER BY final_priority_score DESC;
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, con=conn)
    return df

@st.cache_data
def get_available_dates():
    """대시보드 상단 날짜 필터용 시계열 리스트 추출"""
    engine = get_db_engine()
    query = "SELECT DISTINCT base_date FROM mart_youth_housing_priority ORDER BY base_date DESC;"
    with engine.connect() as conn:
        df = pd.read_sql(query, con=conn)
    return df['base_date'].tolist()

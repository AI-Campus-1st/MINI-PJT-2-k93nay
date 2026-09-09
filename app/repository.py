# app/repository.py
import pandas as pd
import sqlalchemy
import urllib.parse
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

def get_db_engine():
    """대시보드 조회를 위한 로컬 MariaDB 엔진 연결"""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    db_password = os.getenv("PASSWORD")
    if not db_password:
        st.error(".env 파일에서 PASSWORD를 찾을 수 없습니다.")
        st.stop()

    safe_password = urllib.parse.quote_plus(db_password)
    # 최초의 로컬 MariaDB 3306 포트 주소 복원
    db_url = f"mysql+pymysql://analyst:{safe_password}@localhost:3306/housing_db"
    return sqlalchemy.create_engine(db_url)

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

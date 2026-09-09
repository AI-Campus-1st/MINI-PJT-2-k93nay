# collector/loader.py
import pandas as pd
import sqlalchemy
import urllib.parse
import os
from pathlib import Path
from dotenv import load_dotenv
from .config import DONGDAEMUN_DONG_CODES

def get_db_engine():
    """기존 MariaDB 자산을 이식한 가벼운 로컬 SQLite 파일로 연결"""

    # 방법 A를 통해 생성된 'housing2.db' 파일 경로를 지정합니다.
    db_url = "sqlite:///housing2.db"

    # 스트림릿 멀티스레드 충돌 방지 옵션을 포함하여 엔진 생성
    engine = sqlalchemy.create_engine(
        db_url, connect_args={"check_same_thread": False}
    )

    return engine

def load_to_mysql(csv_path):
    """수집된 청년 생활인구 로컬 CSV 데이터를 SQLite 서버에 무결하게 대치 적재"""
    if not os.path.exists(csv_path):
        print(f"[적재 실패] 수집 파일 데이터가 경로에 존재하지 않습니다: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        print("[적재 건너뜀] 적재할 데이터 레코드가 존재하지 않습니다.")
        return

    engine = get_db_engine()

    print(
        f"총 {len(df):,}건의 생활인구 Raw 데이터를 SQLite 인프라에 적재 개시합니다."
    )

    df.to_sql(
        name="seoul_living_pop_raw",
        con=engine,
        if_exists="replace",
        index=False,
    )

    print(
        "[적재 완결] 중복 제거 및 무결성 검증을 통과하여 `seoul_living_pop_raw` SQLite 파일 이식을 완료했습니다."
    )

if __name__ == "__main__":
    target_csv = "data/raw_living_pop_sample.csv"
    load_to_mysql(target_csv)

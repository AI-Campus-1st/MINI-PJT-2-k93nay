# collector/loader.py
import pandas as pd
import sqlalchemy
import urllib.parse
import os
from pathlib import Path
from dotenv import load_dotenv
from .config import DONGDAEMUN_DONG_CODES

def get_db_engine():
    """기존 미니프로젝트1 RDBMS 자산을 그대로 연결"""
    # .env 로드 복원
    env_path = Path(__file__).resolve().parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    

    # 미니프로젝트 1번에서 검증 완료한 패스워드 구조 적용
    db_password = os.getenv("PASSWORD")
    if not db_password:
        raise ValueError(".env 파일에서 PASSWORD를 찾을 수 없습니다. 패스워드를 설정해주세요.")
    
    safe_password = urllib.parse.quote_plus(db_password)  
    
    db_url = f'mysql+pymysql://analyst:{safe_password}@localhost:3306/housing_db?local_infile=1'
    engine = sqlalchemy.create_engine(db_url)
    return engine

def load_to_mysql(csv_path):
    """수집된 청년 생활인구 로컬 CSV 데이터를 housing_db 서버에 안전하게 UPSERT 적재"""
    if not os.path.exists(csv_path):
        print(f"[적재 실패] 수집 파일 데이터가 경로에 존재하지 않습니다: {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    if df.empty:
        print("[적재 건너뜀] 적재할 데이터 레코드가 존재하지 않습니다.")
        return
        
    engine = get_db_engine()
    
    # RDBMS 무결성을 위한 원자적 트랜잭션 수동 개시
    with engine.connect() as conn:
        print(f"총 {len(df):,}건의 생활인구 Raw 데이터를 RDBMS 인프라에 적재 개시합니다.")
        
        # 중복 키 충돌 시 새로운 데이터로 덮어쓰는(UPSERT) 순수 SQL 엔진 전환 이식
        for idx, row in df.iterrows():
            upsert_query = sqlalchemy.text("""
                INSERT INTO seoul_living_pop_raw (base_date, hour, dong_code, dong_name, total_pop, youth_pop)
                VALUES (:base_date, :hour, :dong_code, :dong_name, :total_pop, :youth_pop)
                ON DUPLICATE KEY UPDATE
                    total_pop = VALUES(total_pop),
                    youth_pop = VALUES(youth_pop);
            """)
            
            conn.execute(upsert_query, {
                "base_date": str(row["base_date"]),
                "hour": int(row["hour"]),
                "dong_code": str(row["dong_code"]),
                "dong_name": str(row["dong_name"]),
                "total_pop": float(row["total_pop"]),
                "youth_pop": float(row["youth_pop"])
            })
            
        conn.commit()
    print("[적재 완결] 중복 제거 및 무결성 검증을 통과하여 `seoul_living_pop_raw` 테이블 이식을 완료했습니다.")

if __name__ == "__main__":
    target_csv = "data/raw_living_pop_sample.csv"
    load_to_mysql(target_csv)

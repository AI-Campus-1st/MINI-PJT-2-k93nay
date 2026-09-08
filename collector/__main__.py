# collector/__main__.py
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from .config import BASE_URL
from .client import make_session
from .gather_living_pop import fetch_living_pop_day_raw  
from .transform import transform_and_filter_youth         
from .loader import load_to_mysql 

def run_pipeline():
    print("=========================================================================")
    print("[BATCH] 동대문구 청년 생활인구 60일 대량 시계열 자동 수집 파이프라인 개시")
    print("=========================================================================")
    
    # 1. 오늘 기준 과거 60일간의 시계열 날짜 목록 목록 자동 생성
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    date_list = [(start_date + timedelta(days=x)).strftime("%Y%m%d") for x in range((end_date - start_date).days + 1)]
    
    session = make_session()
    
    csv_file_path = "data/raw_living_pop_sample.csv"
    os.makedirs("data", exist_ok=True)
    
    # 2. 날짜별 시계열 축 순회 가동
    for idx, target_date in enumerate(date_list):
        print(f"\n[{idx+1}/{len(date_list)}] {target_date} 일자 프로세스 처리 중...")
        
        # [단계 1: 수집 계층] 가벼워진 gather_living_pop 모듈 호출하여 생 데이터 확보
        day_raw_rows = fetch_living_pop_day_raw(session, BASE_URL, target_date)
        
        if not day_raw_rows:
            print(f"{target_date} 일자는 API 서버에 데이터가 없거나 비어있어 건너뜁니다.")
            continue
            
        # [단계 2: 정제 계층] transform 모듈 호출하여 동대문구 14개동 청년 점유율 연산
        cleaned_data = transform_and_filter_youth(day_raw_rows)
        
        if cleaned_data:
            df = pd.DataFrame(cleaned_data)
            mode = 'w' if idx == 0 else 'a'
            header = True if idx == 0 else False
            
            # data/ 폴더 내 깨끗한 CSV 데이터 누적
            df.to_csv(csv_file_path, mode=mode, index=False, header=header, encoding="utf-8-sig")
            print(f"💾 {target_date} 정제 데이터 로컬 CSV 누적 성공! ({len(df)}건)")
            
        time.sleep(1)
        
    print("\n[수집/정제 완결] 2개월 시계열 데이터가 data/raw_living_pop_sample.csv에 통합되었습니다.")
    print(" RDBMS Warehouse 적재 계층으로 데이터 인트라 이식을 개시합니다.")
    
    # [단계 3: 적재 계층] loader 모듈 호출하여 RDBMS에 중복 없는 UPSERT 최종 적재
    load_to_mysql(csv_file_path)
    
    print("\n=========================================================================")
    print("[BATCH SUCCESS] 수집-정제-적재 파이프라인 전체 프로세스가 정상 완결되었습니다.")
    print("=========================================================================")

if __name__ == "__main__":
    run_pipeline()


# collector/gather_living_pop.py
import requests
import time
from .client import fetch_api_data

def fetch_living_pop_day_raw(session, base_url, target_date):
    """
    특정 날짜의 서울시 전체 생활인구 API를 페이지별(1000개 단위)로 호출하여
    정제하지 않은 순수 원본(Raw) 로우 데이터 배열을 수집해 반환
    """
    day_raw_rows = []
    start_index = 1
    end_index = 1000
    
    while True:
        # 공공데이터포털/열린데이터광장 규격에 맞춘 페이징 URL 빌드
        url = f"{base_url}{start_index}/{end_index}/{target_date}"
        print(f"API 호출 중... [구간: {start_index} ~ {end_index}]")
        
        # collector/client.py의 안전 호출기 사용
        json_data = fetch_api_data(session, url, sleep_time=0.3)
        
        # 더 이상 가져올 데이터가 없거나 에러가 나면 페이지 루프 종료
        if not json_data or "Spop250mLocalResdDong" not in json_data:
            break
            
        rows = json_data["Spop250mLocalResdDong"]["row"]
        if not rows:
            break
            
        # 생 데이터를 정제 없이 그대로 배열에 누적
        day_raw_rows.extend(rows)
        
        # 다음 페이지 구간 세팅
        start_index += 1000
        end_index += 1000
        
        # 하루 행정동 전체 데이터 한계선 도달 시 강제 종료 (안전장치)
        if start_index > 11000:
            break
            
    return day_raw_rows

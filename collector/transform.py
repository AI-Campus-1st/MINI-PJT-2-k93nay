# collector/transform.py
from datetime import datetime
from .config import DONGDAEMUN_DONG_CODES

def transform_and_filter_youth(api_rows):
    cleaned_rows = []
    current_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for r in api_rows:
        raw_dong_code = str(r.get("H_DNG_CD", r.get("H_DONG_CD", ""))).strip()
        target_code = raw_dong_code[:8]
        
        # 화이트리스트 필터링: 오직 config.py에 등록된 동대문구 14개 코드만 판정
        if target_code in DONGDAEMUN_DONG_CODES:
            try:
                # 20대, 30대 남녀 인구수 컬럼만 추출하여 정밀 합산 (결측치는 0 처리)
                youth_pop = (
                    float(r.get("M20", 0)) + float(r.get("M25", 0)) +
                    float(r.get("M30", 0)) + float(r.get("M35", 0)) +
                    float(r.get("F20", 0)) + float(r.get("F25", 0)) +
                    float(r.get("F30", 0)) + float(r.get("F35", 0))
                )
            except (ValueError, TypeError):
                youth_pop = 0
                
            cleaned_rows.append({
                "base_date": str(r.get("YMD")),
                "hour": int(r.get("TT", 0)),
                "dong_code": target_code,
                "dong_name": DONGDAEMUN_DONG_CODES[target_code],
                "total_pop": float(r.get("SPOP", 0)),
                "youth_pop": youth_pop,
                "collected_at": current_now
            })
            
    return cleaned_rows

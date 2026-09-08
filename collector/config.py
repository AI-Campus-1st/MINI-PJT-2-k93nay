# collector/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 환경 변수에서 키 읽어오기 (없으면 에러 메시지 출력)
API_KEY = os.getenv("SEOUL_API_KEY")
if not API_KEY:
    raise ValueError(".env 파일에서 SEOUL_API_KEY를 찾을 수 없습니다. 올바른 인증키를 설정해주세요.")

# 서울시 생활인구 API 기본 URL 설정
BASE_URL = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/Spop250mLocalResdDong/"

# 동대문구 관할 14개 행정동 코드 매핑
DONGDAEMUN_DONG_CODES = {
    "11230536": "용신동",
    "11230545": "제기동",
    "11230560": "전농1동",
    "11230570": "전농2동",
    "11230600": "답십리1동",
    "11230610": "답십리2동",
    "11230650": "장안1동",
    "11230660": "장안2동",
    "11230710": "청량리동",
    "11230720": "회기동",
    "11230730": "휘경1동",
    "11230740": "휘경2동",
    "11230745": "이문1동",
    "11230750": "이문2동"
}

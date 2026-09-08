# collector/client.py
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def make_session(retries=3, backoff=0.5):
    """네트워크 장애 및 Rate Limit 초과 시 자동 재시도를 수행하는 세션 빌더"""
    s = requests.Session()
    retry = Retry(
        total=retries, 
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s

def fetch_api_data(session, url, sleep_time=0.3):
    """안전 딜레이(Time Sleep)가 내장된 공통 HTTP GET 호출기"""
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        time.sleep(sleep_time) 
        return response.json()
    except Exception as e:
        print(f"[네트워크 호출 에러] URL: {url} | 사유: {e}")
        return None

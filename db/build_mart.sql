-- =========================================================================
-- [최종] 대시보드 전용 집계 데이터 마트 (App 조회 전용)
-- 디자인 규칙: 오픈 API 시계열 날짜와 8자리 행정동 코드를 결합한 마트 테이블
-- =========================================================================

CREATE TABLE mart_youth_housing_priority (
    base_date               VARCHAR(8) NOT NULL,   -- 수집 기준일자
    dong_code               VARCHAR(8) NOT NULL,   -- 8자리 행정동코드
    dong_name               VARCHAR(50) NOT NULL,  -- 행정동명
    avg_youth_pop           DOUBLE,                -- 해당 동의 일평균 청년 생활인구 (절대 수요)
    
    -- 지표 1. 상대적 청년 밀도 지표
    youth_occupancy_rate    DOUBLE,                -- 청년 생활인구 점유율 (청년인구 / 총생활인구) -> 공실 방어를 위한 정규화 지표
    
    -- 지표 2. 절대 인구수 기반의 미니프로젝트1 가중치 결합 점수
    final_volume_score      DOUBLE,                -- 절대 청년 인구수 기반의 인프라 가중치 합산 점수 (절대 규모 축)
    
    -- 지표 3. [최종 목표] 절대 점수도 높고, 상대 비율도 높은 곳을 짚어내는 교차 결합 지표
    final_priority_score    DOUBLE,                -- 상대밀도(Density, 지표1) X 절대규모(Volume, 지표2) 최종 유망도 종합 점수
    PRIMARY KEY (base_date, dong_code)
);


-- =========================================================================
-- 원본 데이터 결합 및 파생지표 연산 후 데이터 마트 주입 (UPSERT)
-- 무거운 GROUP BY 및 JOIN을 사전에 완료하여 대시보드 속도를 최적화합니다.
-- =========================================================================

-- 1단계: 기존 동별 기초 일평균 및 점유율 집계 (임시)

DROP TABLE IF EXISTS temp_dong_daily_summary;

CREATE TABLE temp_dong_daily_summary (
    base_date            VARCHAR(8),
    dong_code            VARCHAR(8),
    dong_name            VARCHAR(50),
    daily_avg_youth      DOUBLE,
    occupancy_rate       DOUBLE,
    PRIMARY KEY (base_date, dong_code)
);


INSERT INTO temp_dong_daily_summary (base_date, dong_code, dong_name, daily_avg_youth, occupancy_rate)
SELECT 
    base_date,
    dong_code,
    dong_name,
    AVG(youth_pop) AS daily_avg_youth,
    ROUND(AVG(youth_pop) / AVG(total_pop), 4) AS occupancy_rate
FROM seoul_living_pop_raw
WHERE dong_name IS NOT NULL
GROUP BY base_date, dong_code, dong_name;




-- 2단계: 원 최대값(Max) 산출용 임시 테이블 생성 (임시)

DROP TABLE IF EXISTS temp_raw_scores;

CREATE TABLE temp_raw_scores (
    base_date           VARCHAR(8),
    dong_code           VARCHAR(8),
    dong_name           VARCHAR(50),
    avg_youth_pop       DOUBLE,
    youth_occupancy_rate DOUBLE,
    raw_volume_score    DOUBLE,
    raw_priority_score  DOUBLE,
    PRIMARY KEY (base_date, dong_code)
);

INSERT INTO temp_raw_scores
SELECT 
    t.base_date,
    t.dong_code,
    t.dong_name,
    ROUND(t.daily_avg_youth, 2) AS avg_youth_pop,
    t.occupancy_rate AS youth_occupancy_rate,
    -- 정규화 전 원본 절대 규모 점수
    ((t.daily_avg_youth * m.면적당_노후주택수) * 0.34) + ((t.daily_avg_youth * m.면적당_좁은도로수) * 0.33) + ((t.daily_avg_youth * m.면적당_자율주택대상수) * 0.33) AS raw_volume_score,
    -- 정규화 전 원본 최종 종합 스코어
    (((t.daily_avg_youth * m.면적당_노후주택수) * 0.34) + ((t.daily_avg_youth * m.면적당_좁은도로수) * 0.33) + ((t.daily_avg_youth * m.면적당_자율주택대상수) * 0.33)) * t.occupancy_rate AS raw_priority_score
FROM temp_dong_daily_summary t
CROSS JOIN (
    SELECT 
        r.district_name,
        ROUND(CAST(o.old_housing_total AS DOUBLE) / r.area_km2, 2) AS 면적당_노후주택수,
        ROUND(CAST(a.target_building_count AS DOUBLE) / r.area_km2, 2) AS 면적당_자율주택대상수,
        ROUND(CAST(COUNT(rd.road_id) AS DOUBLE) / r.area_km2, 2) AS 면적당_좁은도로수
    FROM seoul_region r
        JOIN old_housing_status o ON r.district_name = o.district_name
        JOIN autonomous_renewal_target a ON r.district_name = a.district_name
        LEFT JOIN road_segment rd ON r.district_name = rd.district_name
    WHERE r.district_name = '동대문구' AND rd.road_width >= 4 AND rd.road_width < 6
    GROUP BY r.district_name, r.area_km2, o.old_housing_total, a.target_building_count
) m;


-- 3단계: 일자별 최고점을 1,000점으로 맵핑하여 데이터 마트 최종 주입 (REPLACE INTO)

TRUNCATE TABLE mart_youth_housing_priority;

REPLACE INTO mart_youth_housing_priority (
    base_date, dong_code, dong_name, avg_youth_pop, 
    youth_occupancy_rate, final_volume_score, final_priority_score
)
SELECT 
    r.base_date,
    r.dong_code,
    r.dong_name,
    r.avg_youth_pop,
    r.youth_occupancy_rate,
    
    -- [절대 규모 점수 변환] 일별 1등 원점수를 1,000점으로 맵핑하여 소수점 3자리 절대 규모 점수 정규화
    ROUND((r.raw_volume_score / mx.max_vol) * 1000, 3) AS final_volume_score,
    
    -- [최종 종합 스코어 변환] 종합 점수 역시 최고점을 1,000점 기준으로 점수 정규화
    ROUND((r.raw_priority_score / mx.max_prio) * 1000, 3) AS final_priority_score
FROM temp_raw_scores r
JOIN (
    -- 일별 최고 원점수(MAX)들을 서브쿼리로 추출
    SELECT 
        base_date,
        MAX(raw_volume_score) AS max_vol,
        MAX(raw_priority_score) AS max_prio
    FROM temp_raw_scores
    GROUP BY base_date
) mx ON r.base_date = mx.base_date;

-- 사용이 끝난 임시 테이블 정리
DROP TABLE IF EXISTS temp_dong_daily_summary;
DROP TABLE IF EXISTS temp_raw_scores;
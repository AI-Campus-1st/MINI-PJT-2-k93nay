-- =========================================================================
-- [프로젝트 DDL 스크립트] 모듈러 기반 자율주택정비사업 최적지 발굴 인프라 구축
-- 파일 경로: project/db/schema.sql
-- 디자인 규칙: 영문 스네이크케이스, 명시적 Primary Key/Foreign Key, 성능 인덱스 배치
-- =========================================================================
=======================================================================================================================
0. 데이터베이스 생성
=======================================================================================================================

CREATE DATABASE housing_db
    CHARACTER SET utf8mb4                        # 한글, 이모티콘까지 저장 가능
    COLLATE utf8mb4_unicode_ci;

-- 데이터 베이스 정상 생성 확인
SHOW DATABASES;

-- 데이터 베이스 사용
USE housing_db;

-- 계정에 모든 권한 부여
GRANT ALL PRIVILEGES ON housing_db.* TO 'analyst'@'localhost';

-- 권한 적용 사항 즉시 반영
FLUSH PRIVILEGES;

-- 원본 csv 등 로컬파일 사용
SET GLOBAL local_infile = 1;

=======================================================================================================================
1. 테이블 생성, 정의, 제약조건, 인덱스 생성
=======================================================================================================================

-- 1. 마스터 테이블
CREATE TABLE seoul_region (
    district_name VARCHAR(50) NOT NULL,    -- 자치구명 (예: '종로구', '강북구' 자체가 PK)
    area_km2 DOUBLE NOT NULL,              -- 자치구 면적 (km²)
    PRIMARY KEY(district_name)
);

-- 2. 주택 현황 및 보급률 테이블
CREATE TABLE housing_status (
    district_name VARCHAR(50) NOT NULL,
    total_housing_count INT NOT NULL,       -- 총 주택 수 (호)
    FOREIGN KEY (district_name) REFERENCES seoul_region(district_name)
);

-- 3. 건축 경과연수별 노후 주택 현황 테이블
CREATE TABLE old_housing_status (
    district_name VARCHAR(50) NOT NULL,
    old_housing_total INT NOT NULL,   -- 30년 이상 노후 주택 수 계
    old_detached_house INT NOT NULL,  -- 노후 단독주택 수
    old_row_house INT NOT NULL,       -- 노후 연립주택 수
    old_apartment_house INT NOT NULL, -- 노후 다세대주택 수
    FOREIGN KEY (district_name) REFERENCES seoul_region(district_name)
);

-- 4. 도로 구간 정보 테이블
CREATE TABLE road_segment (
    road_id INT AUTO_INCREMENT,
    district_name VARCHAR(50) NOT NULL,          
    road_name VARCHAR(255),                 -- 도로명 (RN)
    road_width DOUBLE,                      -- 도로 폭 (ROAD_BT)
    road_length DOUBLE,                     -- 도로 길이 (ROAD_LT)
    PRIMARY KEY(road_id),
    FOREIGN KEY (district_name) REFERENCES seoul_region(district_name)
);


--- 4번 실행을 위한 임시 테이블
--CREATE TABLE temp_road_raw (
--    col1 TEXT,  col2 TEXT,  col3 TEXT,  col4 TEXT,  col5 TEXT,  
--    col6 TEXT,  col7 TEXT,  col8 TEXT,  col9 TEXT,  col10 TEXT,
--    col11 TEXT, col12 TEXT, col13 TEXT, col14 TEXT, col15 TEXT, 
--    col16 TEXT, col17 TEXT, col18 TEXT, col19 TEXT, col20 TEXT,
--    col21 TEXT, col22 TEXT, col23 TEXT 
--);

-- 5. 자율주택정비사업 대상 건축물 테이블
CREATE TABLE autonomous_renewal_target (
    district_name VARCHAR(50) NOT NULL,
    target_building_count INT NOT NULL, -- 5층 이하 저층 주거용 건축물 수
    FOREIGN KEY (district_name) REFERENCES seoul_region(district_name)
);

--- 5번 실행을 위한 임시 테이블
--CREATE TABLE temp_building_filter (
--    district_raw VARCHAR(100), 
--    main_use VARCHAR(100),     
--    floor_raw VARCHAR(50)      
--);


-- 조인 성능 최적화를 위한 인덱스 생성
CREATE INDEX idx_road_district ON road_segment(district_name);
CREATE INDEX idx_road_width ON road_segment(road_width);

-- =========================================================================
-- [추가 원본 계층] 오픈 API 수집 원본 테이블 (Collector 적재용)
-- 디자인 규칙: 8자리 행정동 코드, 날짜, 시간대를 묶어 중복 수집을 방지하는 복합 PK 구축
-- =========================================================================

CREATE TABLE seoul_living_pop_raw (
    base_date      VARCHAR(8) NOT NULL,   -- '20260901' 형태
    hour           INT NOT NULL,          -- 0 ~ 23시
    dong_code      VARCHAR(8) NOT NULL,   -- 8자리 행정동코드 (PK)
    dong_name      VARCHAR(50) NOT NULL,  -- 행정동명
    total_pop      DOUBLE NOT NULL,       -- 해당 시간대 총 생활인구
    youth_pop      DOUBLE NOT NULL,       -- 2030 청년 생활인구
    collected_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (base_date, hour, dong_code) -- 중복 적재 방지를 위한 유니크 복합 키
);

-- 대시보드 조회 속도 향상 및 데이터 마트(Mart) 빌드 가속화를 위한 결합 인덱스
CREATE INDEX idx_pop_date_dong ON seoul_living_pop_raw(base_date, dong_code);

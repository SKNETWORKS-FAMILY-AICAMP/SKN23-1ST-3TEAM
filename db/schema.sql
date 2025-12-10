-- # 테이블 생성 스크립트

-- create database cardb;
-- 
-- CREATE USER 'smc'@'%' IDENTIFIED BY  '1234';
-- 
-- GRANT ALL PRIVILEGES ON bookdb.* TO 'smc'@'%';
-- 
-- SHOW GRANTS FOR 'smc'@'%';


use cardb;


drop table if exists scrapped;

drop table if exists registered;


-- car tables
create table scrapped		-- 폐차된 차량 테이블
(
	sc_id int auto_increment primary key,
	scity varchar(10) comment '도시',
	scar_count int comment '차량 개수',
	scar_type varchar(10) comment '차 종류',
	syear varchar(10) comment '폐차된 년도',
	stotal int comment '총 차량'
) engine=innodb;
-- 
create table registered		-- 등록된 차량 테이블
(
	rc_id int auto_increment primary key,
	rcity varchar(10) comment '도시',
	rcar_count int comment '차량 개수',
	rcar_type varchar(10) comment '차 종류',
	ryear varchar(10) comment '등록된 년도'
) engine=innodb;




drop table if exists faq_tbl;

drop table if exists subcategory_tbl;

drop table if exists category_tbl;

-- 유형구분 테이블
create table category_tbl
(
	c_code varchar(10) primary key,	-- value = [A00100, A00200, A00300, A00400]
	c_name varchar(10)		-- name = ['상품/가입', '유지/환급', '보상', '기타']
) engine=innodb;

-- 단계구분 테이블
create table subcategory_tbl
(
	s_code varchar(10) primary key,
	c_code varchar(10),
	s_name varchar(50),
    foreign key (c_code) references category_tbl (c_code)
) engine=innodb;

-- value = [A00101, A00102, A00103, A00104, A00105]
-- name = ['상품내용', '보험료/보험가입경력', '모집질서', '계약인수/취소/무효', '계약전 알릴의무 위반']

-- value = [A00201, A00202, A00203, A00204, A00205]
-- name = ['만기/갱신안내', '실효/부활', '계약 변경사항', '해지/환급금', '계약후 통지의무 위반']

-- value = [A00301, A00302, A00303, A00304, A00305]
-- name = ['보험금 청구/사고조사', '사고인과관계/과실 분쟁', '보상금액 기준', '보상여부(면/부책)', '보험금 지급지연']



-- faq tables
create table faq_tbl		-- 보험 자주묻는질문 테이블
(
	id int primary key,
	c_code varchar(10) comment '유형구분',			-- 유형구분 [A00100, ...]
	s_code varchar(10) comment '단계구분',		-- 단계구분 [A00101, ...]
	question varchar(1000) comment '질문',
    answer varchar(1000) comment '답변',
    foreign key (c_code) references subcategory_tbl (c_code),
    foreign key (s_code) references subcategory_tbl (s_code)
) engine=innodb;





-- select 절

select * from scrapped;

select * from registered;

select * from faq_tbl;

select * from category_tbl;

select * from subcategory_tbl;
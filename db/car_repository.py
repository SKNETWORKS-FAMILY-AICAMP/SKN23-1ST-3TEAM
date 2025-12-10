#자동차 데이터 crud

import pandas as pd
import mysql.connector

# MySQL 연결 설정
connection = mysql.connector.connect(
    host = "localhost",         # MySQL 서버 주소
    user = "root",              # 사용자 이름
    password = "1234",          # 비밀번호
    database = "cardb"    # 사용할 데이터베이스
)

cursor = connection.cursor() # 데이터베이스 작업을 위한 커서 객체 생성

### ------------------------------
### 1. scrapped 데이터 삽입
### ------------------------------

# CSV 불러오기
df = pd.read_csv("../data/raw/car_removal.csv")

# 데이터 삽입 쿼리
sql = """
INSERT IGNORE INTO scrapped (scity, scar_count, scar_type, syear, stotal)
values (%s, %s, %s, %s, %s);
""" # 사용자 데이터를 추가하는 SQL 쿼리

for _, row in df.iterrows():
    values = (row['시도별'], row['폐차'], row['차종별'], row['연도'], row['전체 말소'])
    cursor.execute(sql, values) # 쿼리 설정

### ------------------------------
### 2. registered 데이터 삽입
### ------------------------------

# CSV 불러오기
df = pd.read_csv("../data/raw/car_reg.csv")

# 데이터 삽입 쿼리
sql = """
INSERT IGNORE INTO registered (rcity, rcar_count, rcar_type, ryear)
values (%s, %s, %s, %s);
""" # 사용자 데이터를 추가하는 SQL 쿼리

for _, row in df.iterrows():
    values = (row['시도별'], row['등록'], row['차종별'], row['연도'])
    cursor.execute(sql, values) # 쿼리 설정

### ------------------------------
# 저장하고 종료
### ------------------------------

connection.commit()         # 변경사항 커밋
cursor.close()
connection.close()

print("자동차 등록/폐차 테이블 데이터 삽입 완료!")
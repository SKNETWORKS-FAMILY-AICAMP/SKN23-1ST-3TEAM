# faq crud 관련

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
### 1. category_tbl 데이터 삽입
### ------------------------------

# CSV 불러오기
df = pd.read_csv("../data/raw/category_tbl.csv")

# 데이터 삽입 쿼리
sql = """
INSERT IGNORE INTO category_tbl (c_code, c_name)
values (%s, %s);
""" # 사용자 데이터를 추가하는 SQL 쿼리

for _, row in df.iterrows():
    values = (row['c_code'], row['c_name'])
    cursor.execute(sql, values) # 쿼리 설정

### ------------------------------
### 2. subcategory_tbl 데이터 삽입
### ------------------------------

# CSV 불러오기
df = pd.read_csv("../data/raw/subcategory_tbl.csv")

# 데이터 삽입 쿼리
sql = """
INSERT IGNORE INTO subcategory_tbl (s_code, c_code, s_name)
values (%s, %s, %s);
""" # 사용자 데이터를 추가하는 SQL 쿼리

for _, row in df.iterrows():
    values = (row['s_code'], row['c_code'], row['s_name'])
    cursor.execute(sql, values) # 쿼리 설정

### ------------------------------
### 3. faq_tbl 데이터 삽입
### ------------------------------

# CSV 불러오기
df = pd.read_csv("../data/raw/insurance_faq.csv")

# 데이터 삽입 쿼리
sql = """
INSERT IGNORE INTO faq_tbl (id, c_code, s_code, question, answer)
values (%s, %s, %s, %s, %s);
""" # 사용자 데이터를 추가하는 SQL 쿼리

for _, row in df.iterrows():
    values = (row['id'], row['c_code'], row['s_code'], row['question'], row['answer'])
    cursor.execute(sql, values) # 쿼리 설정

### ------------------------------
# 저장하고 종료
### ------------------------------

connection.commit()         # 변경사항 커밋
cursor.close()
connection.close()

print("FAQ 테이블 데이터 삽입 완료!")
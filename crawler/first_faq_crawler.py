import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time

# 1. 기본 설정
BASE_URL = "https://consumer.knia.or.kr/consumer/center/faq.do?first=A00000"

driver = webdriver.Chrome()
driver.get(BASE_URL)

# 251209 정석원 작업(첨부터 끝까지)

# 2. CSV용 컨테이너 초기화
# category_tbl 용
# 유형 구분에 대한 정보를 저장하는 딕셔너리
category_rows = {}   # {c_code: {"c_code": ..., "c_name": ...}}
# subcategory_tbl 용
# 단계 구분에 대한 정보를 저장하는 딕셔너리
subcategory_rows = {}   # {s_code: {"s_code": ..., "c_code": ..., "s_name": ...}}
# insurance_faq 용
# faq 데이터(질문/답변)을 담을 리스트
faq_rows = []        # [{"id":..., "c_code":..., "s_code":..., "question":..., "answer":...}, ...]

# 3. 유형구분 전체 목록 읽기 (select#second)
# driver.find_element(By.ID, "second")
# html에서 id= second인 <select> 요소를 찾는다(드롭다운 형식)
# Select
# selenium의 select 클래스로 감싸서 .options, .select_by_value()같은 편의 기능 사용
type_select = Select(driver.find_element(By.ID, "second")) 
# 나중에 value, text 튜플들을 모아둘 리스트
type_options = []

# 유형구분 옵션값 for문으로 뽑아오기 
# <select> 내부의 옵션 태그 리스트
for opt in type_select.options:
    # 각 옵션의 value값 추출후 공백 제거(A00100)
    val = opt.get_attribute("value").strip()
    # 화면에 보이는 옵션 이름의 텍스트 추출(상품/가입)
    txt = opt.text.strip()
    # value가 비어있는 첫 번째 placeholder(유형구분) 건너뛰기
    if not val:
        continue
    # 유형 코드와 이름을 튜플로 리스트에 저장
    type_options.append((val, txt))
    # csv로 만들기 쉽게 dict형태로 저장
    category_rows[val] = {
        "c_code": val,
        "c_name": txt
    }

print("[유형구분 목록]")
for code, name in type_options:
    print(code, "|", name)
print()

# 각 유형별로 단계 → FAQ 크롤링
# 앞에서 수집한 모든 유형(c_code, c_name) 각각에 반복
for c_code, c_name in type_options:
    # 매번 첫 화면부터 시작하는 게 안정적(페이지 상태 꼬임 방지)
    driver.get(BASE_URL)
    time.sleep(1)

    # 1) 해당 유형 선택
    # id="second" 즉, second라는 select id요소를 찾아서 select 객체로 생성
    type_select = Select(driver.find_element(By.ID, "second"))
    # 현재 루프의 유형 코드에 해당하는 옵션 선택
    type_select.select_by_value(c_code)
    time.sleep(0.5)

    # 2) third 옵션이 채워질 때까지 기다리기
    # WebDriverWait에서 쓸 콜백 함수
    def third_has_options(d):
        # id는 third요소를 찾아 select 한 후 옵션 개수가 1개보다 많으면 true 반환-> 단계구분 옵션이 채워졌다는 의미
        sel = Select(d.find_element(By.ID, "third"))
        return len(sel.options) > 1
    
    # 최대 10초동안 윗 함수가 true가 될때까지 대기
    try:
        WebDriverWait(driver, 10).until(third_has_options)
    # 10초내에 채워지지않으면 타임아웃
    except TimeoutException:
        print(f"[유형 {c_code}] 단계 옵션 없음 → 스킵")
        continue  

    # 3) 단계구분 옵션 읽기
    # id="third"인 단계 구분의 <select>요소를 select로 래핑
    step_select = Select(driver.find_element(By.ID, "third"))
    step_options = []
    
    # 모든 옵션 리스트
    for opt in step_select.options:
        # 단계코드
        s_val = opt.get_attribute("value").strip()
        # 단계 이름
        s_txt = opt.text.strip()
        # value가 비어 있는 placeholder는 건너뜀
        if not s_val:  # "단계구분" placeholder 제외
            continue
        # 단계 코드/이름을 step_options 리스트에 저장
        step_options.append((s_val, s_txt))
        # s_code,c_code,s_name에 저장
        subcategory_rows[s_val] = {
            "s_code": s_val,
            "c_code": c_code,
            "s_name": s_txt
        }

    print(f"\n=== 유형 {c_name} ({c_code}) ===")
    print("단계구분:", step_options)

    # 4) 각 단계별로 검색 → FAQ 수집
    # 현재 유형에 속한 모든 단계 각각에 대해 반복
    for s_code, s_name in step_options:
        # 유형/단계를 매번 다시 선택 (상태 꼬임 방지)
        # 루프마다 다시 : second select에서 c_code(유형)선택
        type_select = Select(driver.find_element(By.ID, "second"))
        type_select.select_by_value(c_code)
        WebDriverWait(driver, 10).until(third_has_options)

        step_select = Select(driver.find_element(By.ID, "third"))
        step_select.select_by_value(s_code)
        time.sleep(1)

        # 조회 버튼 클릭
        search_btn = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        search_btn.click()

        try:
            # 결과 로딩 대기 (FAQ가 없으면 Timeout 가능)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.faqWrap"))
            )
        except TimeoutException:
            print(f"[유형 {c_code} / 단계 {s_code}] FAQ 영역 없음 → 스킵")
            continue

        # 여기서부터는 BeautifulSoup으로 파싱
        # 현재 페이지의 전체 html소스를 문자열로 가져옴
        page_html = driver.page_source
        # HTML을 파싱해서 BeautifulSoup 객체 생성.
        soup = BeautifulSoup(page_html, "html.parser")
        # ul태그 중 class가 faqwrap인 리스트 안의 class faqAc를 가진 li요소들을 전부 선택
        # -> 각 faq항목 하나
        faq_items = soup.select("ul.faqWrap li.faqAc")

        if not faq_items:
            print(f"[유형 {c_code} / 단계 {s_code}] FAQ 없음")
            continue

        print(f"\n[유형 {c_code} / 단계 {s_code} ({s_name})] FAQ 개수:", len(faq_items))

        for idx, li in enumerate(faq_items, start=1):
            # 질문 제목 영역을 나타내는 <a>태그 atit 찾기
            q_tag = li.select_one("a.aTit")
            # 답변이 들어있는 div태그 answer 클래스 찾기
            a_tag = li.select_one("div.answer")
            if not q_tag or not a_tag:
                continue
            # 질문 텍스트를 공백 제거로 가져옴
            q = q_tag.get_text(strip=True)
            # <a>태그의 faqidx속성값 가져오기(faq를 구분하는 고유 id로 사용)
            faqidx = q_tag.get("faqidx")  # 원본 속성명
            # 답변 텍스트를 가져오되 태그 사이 줄바꿈은 \n으로 바꾸고 공백 제거
            a = a_tag.get_text("\n", strip=True)  # 줄바꿈 유지

            # faqidx가 없으면 스킵 (PK로 쓸 예정이니까)
            if not faqidx:
                continue
            
            faq_rows.append({
                "id": int(faqidx),   # ← PK로 쓸 컬럼
                "c_code": c_code,
                "s_code": s_code,
                "question": q,
                "answer": a
            })

        time.sleep(2)

driver.quit()

# ----------------- CSV 저장 -----------------

# category_tbl 용
df_category = pd.DataFrame(list(category_rows.values()))
df_category = df_category.sort_values("c_code")
df_category.to_csv("../data/raw/category_tbl.csv", index=False, encoding="utf-8-sig")

# subcategory_tbl 용
df_subcategory = pd.DataFrame(list(subcategory_rows.values()))
df_subcategory = df_subcategory.sort_values(["c_code", "s_code"])
df_subcategory.to_csv("../data/raw/subcategory_tbl.csv", index=False, encoding="utf-8-sig")

# insurance_faq 용
df_faq = pd.DataFrame(faq_rows)
df_faq = df_faq.sort_values(["id", "c_code", "s_code"])
df_faq.to_csv("../data/raw/insurance_faq.csv", index=False, encoding="utf-8-sig")

print("CSV 저장 완료: category_tbl.csv, subcategory_tbl.csv, insurance_faq.csv")

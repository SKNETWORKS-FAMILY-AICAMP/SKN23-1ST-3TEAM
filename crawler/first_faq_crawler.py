import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time

BASE_URL = "https://consumer.knia.or.kr/consumer/center/faq.do?first=A00000"

driver = webdriver.Chrome()
driver.get(BASE_URL)

# 251209 정석원 작업(첨부터 끝까지)

# CSV용 컨테이너
# category_tbl 용
category_rows = {}   # {c_code: {"c_code": ..., "c_name": ...}}
# subcategory_tbl 용
subcategory_rows = {}   # {s_code: {"s_code": ..., "c_code": ..., "s_name": ...}}
# insurance_faq 용
faq_rows = []        # [{"id":..., "c_code":..., "s_code":..., "question":..., "answer":...}, ...]

# 0) 유형구분 전체 목록 읽기 (select#second)
type_select = Select(driver.find_element(By.ID, "second"))
type_options = []

# 유형구분 옵션값 for문으로 뽑아오기 
for opt in type_select.options:
    val = opt.get_attribute("value").strip()
    txt = opt.text.strip()
    if not val:  # "유형구분" placeholder 제외
        continue
    type_options.append((val, txt))
    category_rows[val] = {
        "c_code": val,
        "c_name": txt
    }

print("[유형구분 목록]")
for code, name in type_options:
    print(code, "|", name)
print()

# 각 유형별로 단계 → FAQ 크롤링
for c_code, c_name in type_options:
    # 매번 첫 화면부터 시작하는 게 안정적
    driver.get(BASE_URL)
    time.sleep(1)

    # 1) 해당 유형 선택
    type_select = Select(driver.find_element(By.ID, "second"))
    type_select.select_by_value(c_code)
    time.sleep(0.5)

    # 2) third 옵션이 채워질 때까지 기다리기
    def third_has_options(d):
        sel = Select(d.find_element(By.ID, "third"))
        return len(sel.options) > 1

    try:
        WebDriverWait(driver, 10).until(third_has_options)
    except TimeoutException:
        print(f"[유형 {c_code}] 단계 옵션 없음 → 스킵")
        continue  

    # 3) 단계구분 옵션 읽기
    step_select = Select(driver.find_element(By.ID, "third"))
    step_options = []
    for opt in step_select.options:
        s_val = opt.get_attribute("value").strip()
        s_txt = opt.text.strip()
        if not s_val:  # "단계구분" placeholder 제외
            continue
        step_options.append((s_val, s_txt))
        subcategory_rows[s_val] = {
            "s_code": s_val,
            "c_code": c_code,
            "s_name": s_txt
        }

    print(f"\n=== 유형 {c_name} ({c_code}) ===")
    print("단계구분:", step_options)

    # 4) 각 단계별로 검색 → FAQ 수집
    for s_code, s_name in step_options:
        # 유형/단계를 매번 다시 선택 (상태 꼬임 방지)
        type_select = Select(driver.find_element(By.ID, "second"))
        type_select.select_by_value(c_code)
        WebDriverWait(driver, 10).until(third_has_options)

        step_select = Select(driver.find_element(By.ID, "third"))
        step_select.select_by_value(s_code)
        time.sleep(1)

        # # 검색어(title)는 비움
        # title_input = driver.find_element(By.ID, "title")
        # title_input.clear()

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
        page_html = driver.page_source
        soup = BeautifulSoup(page_html, "html.parser")
        faq_items = soup.select("ul.faqWrap li.faqAc")

        if not faq_items:
            print(f"[유형 {c_code} / 단계 {s_code}] FAQ 없음")
            continue

        print(f"\n[유형 {c_code} / 단계 {s_code} ({s_name})] FAQ 개수:", len(faq_items))

        for idx, li in enumerate(faq_items, start=1):
            q_tag = li.select_one("a.aTit")
            a_tag = li.select_one("div.answer")
            if not q_tag or not a_tag:
                continue

            q = q_tag.get_text(strip=True)
            faqidx = q_tag.get("faqidx")  # 원본 속성명

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

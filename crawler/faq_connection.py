# crawler/faq_connection.py
from db.connection import connection

def get_category_list():
    """category_tbl에서 전체 유형 코드/이름 가져오기"""
    conn = connection
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c_code, c_name
        FROM category_tbl
        ORDER BY c_code;
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows    # 예: [("A00100", "상품/가입"), ("A00200", "유지/환급"), ...]

def get_subcategory_list():
    """subcategory_tbl에서 전체 단계 코드/이름/유형코드 가져오기"""
    conn = connection
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s_code, s_name, c_code
        FROM subcategory_tbl
        ORDER BY s_code;
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows    # 예: [("S001", "초기", "A00200"), ...]

def get_all_faq():
    """전체 FAQ(question, answer) 가져오기"""
    conn = connection
    cursor = conn.cursor()
    cursor.execute("""
        SELECT question, answer
        FROM faq_tbl
        ORDER BY id;
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows    # [("질문1", "답변1"), ("질문2", "답변2"), ...]


def get_faq_by_category(c_code: str):
    """특정 유형(c_code)에 해당하는 FAQ 목록"""
    conn = connection
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.question, f.answer
        FROM faq_tbl f
        JOIN subcategory_tbl s ON f.s_code = s.s_code
        WHERE s.c_code = %s
        ORDER BY f.id;
    """, (c_code,))
    rows = cursor.fetchall()
    cursor.close()
    return rows

def get_faq_by_step(s_code: str):
    """특정 단계(s_code)에 해당하는 FAQ 목록"""
    conn = connection
    cursor = conn.cursor()
    cursor.execute("""
        SELECT question, answer
        FROM faq_tbl
        WHERE s_code = %s
        ORDER BY id;
    """, (s_code,))
    rows = cursor.fetchall()
    cursor.close()
    return rows

def format_answer(answer: str) -> str:
    """DB에서 가져온 answer 문자열을 요약/상세 구분해서 줄바꿈/강조"""
    if not answer:
        return ""

    text = str(answer).replace("\r\n", "\n")

    # [요약설명], [상세설명]을 굵게 보이게 + 줄바꿈
    text = text.replace("[요약설명]", "\n**[요약설명]**\n")
    text = text.replace("[상세설명]", "\n\n**[상세설명]**\n")

    # 일반 줄바꿈도 Markdown에서 잘 보이도록 처리
    text = text.replace("\n", "  \n")

    return text.strip()

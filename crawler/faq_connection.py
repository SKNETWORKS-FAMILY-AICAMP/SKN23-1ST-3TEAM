# services/faq_service.py
from db.connection import get_connection

def get_category_list():
    """faq_type에서 전체 유형 코드/이름 가져오기"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM category_tbl
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    # print(rows)
    return rows

def get_subcategory_list():
    """선택된 type_code에 해당하는 단계 목록"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s_code, s_name,c_code
        FROM subcategory_tbl
        ORDER BY s_code;
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    print(rows)

    return rows 

if __name__ == "__main__":
    # get_category_list(),
    get_subcategory_list()


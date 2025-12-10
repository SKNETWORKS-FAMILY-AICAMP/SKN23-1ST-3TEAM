import streamlit as st
from crawler.faq_connection import (
    get_category_list,
    get_subcategory_list,
    get_all_faq,
    get_faq_by_category,
    get_faq_by_step,
)

def format_answer(answer: str) -> str:
    if not answer:
        return ""
    text = str(answer).replace("\r\n", "\n")
    text = text.replace("[요약설명]", "\n**[요약설명]**\n")
    text = text.replace("[상세설명]", "\n\n**[상세설명]**\n")
    text = text.replace("\n", "  \n")
    return text.strip()


def run():
    st.header("❓ 기업 FAQ")

    st.markdown("""
        <style>
        .stButton > button {
            margin-top: 28px;
        }
        </style>
    """, unsafe_allow_html=True)

    # -------------------------------
    # 1) 상단 필터 영역: 유형 / 단계 / 검색어
    # -------------------------------
    col1, col2, col3 = st.columns([1, 1, 2])

    # 1-1) 유형 선택
    with col1:
        category_rows = get_category_list()  # [(c_code, c_name), ...]
        category_names = ["전체"] + [c_name for c_code, c_name in category_rows]
        selected_category_name = st.selectbox("유형", category_names)

        if selected_category_name == "전체":
            selected_category_code = None
        else:
            selected_category_code = None
            for c_code, c_name in category_rows:
                if c_name == selected_category_name:
                    selected_category_code = c_code
                    break

    # 1-2) 단계 선택 (유형에 따라 필터)
    with col2:
        subcategory_rows = get_subcategory_list()  # [(s_code, s_name, c_code), ...]
        selected_step_code = None

        if selected_category_code is None:
            step_names = ["전체"]
            selected_step_name = st.selectbox("단계", step_names)
        else:
            filtered_subcategories = [
                (s_code, s_name, c_code)
                for s_code, s_name, c_code in subcategory_rows
                if str(c_code).strip() == str(selected_category_code).strip()
            ]

            if not filtered_subcategories:
                step_names = ["전체"]
                selected_step_name = st.selectbox("단계", step_names)
            else:
                step_names = ["전체"] + [
                    s_name for s_code, s_name, c_code in filtered_subcategories
                ]
                selected_step_name = st.selectbox("단계", step_names)

                if selected_step_name != "전체":
                    for s_code, s_name, c_code in filtered_subcategories:
                        if s_name == selected_step_name:
                            selected_step_code = s_code
                            break

    # 1-3) 검색어 입력
    with col3:
        key_f = st.text_input("질문 검색 (키워드)")

    # -------------------------------
    # 2) 검색 조건 상단에 크게 표시
    # -------------------------------
    category_label = selected_category_name if selected_category_name else "전체"
    step_label = selected_step_name if 'selected_step_name' in locals() else "전체"
    keyword_label = key_f if key_f else "없음"

    st.markdown(
        f"""
        ### 🔎 검색 조건  
        - **유형:** {category_label}  
        - **단계:** {step_label}  
        - **검색어:** {keyword_label}
        """,
        unsafe_allow_html=True,
    )

    st.write("---")

    # -------------------------------
    # 3) 조건에 따라 FAQ 기본 집합 조회
    # -------------------------------
    if selected_category_code is None and selected_step_code is None:
        faq_rows = get_all_faq()
    elif selected_category_code is not None and selected_step_code is None:
        faq_rows = get_faq_by_category(selected_category_code)
    else:
        faq_rows = get_faq_by_step(selected_step_code)

    # 3-1) 검색어 필터 (질문에 키워드 포함)
    if key_f:
        keyword = key_f.lower().strip()
        faq_rows = [
            (q, a)
            for q, a in faq_rows
            if keyword in str(q).lower()
        ]

    page_size = 10
    total = len(faq_rows)

    if total == 0:
        st.warning("해당 조건에 대한 FAQ가 없습니다.")
        return

    max_page = (total - 1) // page_size + 1

    # -------------------------------
    # 4) 현재 페이지 (세션으로 관리)
    # -------------------------------
    if "faq_page" not in st.session_state:
        st.session_state["faq_page"] = 1

    col_prev, col_page, col_next = st.columns([1, 2, 1])

    # 필터 변경 후 페이지 수가 줄어든 경우를 대비해 보정
            
    with col_page:
        # number_input 써도 되고, 싫으면 selectbox로 바꿔도 됨
        new_page = st.number_input(
            "페이지",
            min_value=1,
            max_value=max_page,
            value=st.session_state["faq_page"],
            step=1,
        )
        # 입력값이 바뀌면 세션에 반영
        if new_page != st.session_state["faq_page"]:
            st.session_state["faq_page"] = int(new_page)

    # 2) 여기서 최종 page 확정
    current_page = st.session_state["faq_page"]
    # 현재 페이지 데이터 슬라이스
    start = (current_page - 1) * page_size
    end = start + page_size
    page_rows = faq_rows[start:end]

    st.caption(f"총 {total}건 / 페이지 {current_page} / {max_page}")

    # -------------------------------
    # 5) FAQ 내용 출력
    # -------------------------------
    for question, answer in page_rows:
        with st.expander("**[질문]** : " + str(question)):
            st.markdown(format_answer(answer))

import streamlit as st
from crawler.faq_connection import (
    get_category_list,
    get_subcategory_list,
    get_all_faq,
    get_faq_by_category,
    get_faq_by_step,
)

# DB에서
#   * 보험 FAQ 유형 목록 (category)
#   * 단계 목록 (subcategory)
#   * FAQ 데이터를 가져오고
# 화면 상단에서
#   * “유형” 선택
#   * “단계” 선택
#   * “질문 키워드” 입력을 받는다.
# 선택된 조건에 따라
#   * DB에서 해당하는 FAQ들을 가져오고
#   * 질문에 키워드가 포함된 것만 다시 필터링한 뒤
# 결과를
#   * 페이지당 10개씩
#   * 페이지 번호로 넘겨 보면서
#   * 질문은 접히는 박스(expander), 답변은 마크다운 형식으로 예쁘게 보여준다.


# 1. 답변 텍스트 꾸미기
# 답변이 none이거나 빈 문자열이면 그대로 반환(오류 방지)
def format_answer(answer: str) -> str:
    if not answer:
        return ""
    text = str(answer).replace("\r\n", "\n")
    text = text.replace("[요약설명]", "\n**[요약설명]**\n")
    text = text.replace("[상세설명]", "\n\n**[상세설명]**\n")
    # 마크다운에서 일반 줄바꿈은 안 바뀔수가 있어서 강제 줄바꿈 형식인 '공백 두개 + \n'으로 변환
    text = text.replace("\n", "  \n")
    # 앞뒤 공백 제거 후 반환
    return text.strip()
    # format_answer는 DB에서 온 답변 문자열을, 마크다운으로 예쁘게 보일 수 있게 가공하는 함수

def run():
    st.header("❓ 자동차 보험 FAQ (손해 보험 협회)")

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

    # 상단 영역을 3개의 컬럼으로 나눔(유형 / 단계 / 검색어)
    col1, col2, col3 = st.columns([1, 1, 2])

    # 1-1) 유형 선택
    with col1:
        # db에서 c_code랑 c_name목록 가져옴
        category_rows = get_category_list()  # [(c_code, c_name), ...]
        # 화면에 보여줄 옵션은 전체 + ~
        category_names = ["전체"] + [c_name for c_code, c_name in category_rows]
        # 유저는 전체, 상품/가입~ 이런식으로 이름선택
        selected_category_name = st.selectbox("유형", category_names)
        
        # 전체 선택시 필터없이 전체 검색
        if selected_category_name == "전체":
            selected_category_code = None
        else:
            # 선택한 이름에 해당하는 코드(c_code)를 찾아서 selected_category_code에 저장
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
                # subcategory_rows 중에 
                for s_code, s_name, c_code in subcategory_rows
                # c_code == selected_category_code인 것만 골라서 filtered_subcategories에 저장
                if str(c_code).strip() == str(selected_category_code).strip()
            ]
            # 없으면 단계도 전체만 
            if not filtered_subcategories:
                step_names = ["전체"]
                selected_step_name = st.selectbox("단계", step_names)
            else:
                # 유형에 해당하는 단계가 있다면 전체+단계 이름들을 단계 선택 옵션으로
                step_names = ["전체"] + [
                    s_name for s_code, s_name, c_code in filtered_subcategories
                ]
                selected_step_name = st.selectbox("단계", step_names)
                # 특정 단계 이름을 선택한 경우
                if selected_step_name != "전체":
                    # 해당하는 s_code를 찾아 selected_step_code로 저장
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
    # 화면에 보여주기용
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
    
    # 유형도 선택 안했고 단계도 산책 안했다면 get_all_faq로
    if selected_category_code is None and selected_step_code is None:
        faq_rows = get_all_faq()
    # 유형은 선택했는데 단계는 전체(또는 없음)이면 해당유형에 속한 faq만
    elif selected_category_code is not None and selected_step_code is None:
        faq_rows = get_faq_by_category(selected_category_code)
    else:
    # 단계까지 선택했으면 해당 단계에 속한 faq만
        faq_rows = get_faq_by_step(selected_step_code)

    # 3-1) 검색어 필터 (질문에 키워드 포함)
    if key_f:
        keyword = key_f.lower().strip()
        # 질문 답변 튜플중 질문(q)을 문자열로 바꾸고 소문자로 바꾸어서 keyword가 포함된 것만 남김
        faq_rows = [
            (q, a)
            for q, a in faq_rows
            if keyword in str(q).lower()
        ]
    # DB ->  1차 필터(유형/단계) 후에 질문 텍스트 기반 2차 필터(키워드) 적용하는 구조

    # 페이징을 위한 기본준비
    page_size = 10
    total = len(faq_rows)

    if total == 0:
        st.warning("해당 조건에 대한 FAQ가 없습니다.")
        return
    # 전체 개수와 페이지 사이즈로 최대 페이지 수 계산
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

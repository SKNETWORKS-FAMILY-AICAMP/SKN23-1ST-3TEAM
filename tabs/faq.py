import streamlit as st
import pandas as pd

def run():
    st.header("❓ 기업 FAQ")

    st.markdown("""
        <style>
        .stButton > button {
            margin-top: 28px;
        }
        </style>
    """, unsafe_allow_html=True)

    faq = pd.DataFrame([
        {"유형":"유지/환급","단계":"초기","질문":"자동차 등록은 무엇인가요?","답변":"관할 관청에서 번호판 발급."},
        {"유형":"상품/가입","단계":"중간","질문":"자동차 등록 필요 서류?","답변":"신분증, 계약서, 보험 증명서."},
        {"유형":"유지/환급","단계":"초기","질문":"폐차는 어디서 하나요?","답변":"지정 폐차장에서 가능."},
        {"유형":"기타","단계":"전체","질문":"회사 차량 구매 지원?","답변":"기업 HR 정책에 따름."},
    ])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        type_f = st.selectbox("유형", ["전체"] + list(faq["유형"].unique()))
    with col2:
        step_f = st.selectbox("단계", ["전체"] + list(faq["단계"].unique()))
    with col3:
        key_f = st.text_input("검색어")
    with col4:
        search = st.button("검색")

    if search:
        df = faq.copy()

        if type_f != "전체":
            df = df[df["유형"] == type_f]

        if step_f != "전체":
            df = df[df["단계"] == step_f]

        if key_f:
            df = df[df["질문"].str.contains(key_f, case=False)]

        if len(df) == 0:
            st.warning("검색 결과 없음")
        else:
            for _, row in df.iterrows():
                with st.expander("🔸 " + row["질문"]):
                    st.write(row["답변"])
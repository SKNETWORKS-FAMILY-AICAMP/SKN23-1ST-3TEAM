import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import altair as alt

# -------------------------------
# 페이지 설정
# -------------------------------
st.set_page_config(page_title="자동차 현황 & FAQ & 폐차", layout="wide")

# 타이틀
st.markdown(
    """
    <h1 style='text-align: center; margin-top: 5px; margin-bottom: 40px;'>
        🚗 자동차 등록/폐차 현황 & 기업 FAQ 시스템
    </h1>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# 세션 상태 초기화
# -------------------------------
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "자동차 등록 현황 보기"
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None
if "selected_question" not in st.session_state:
    st.session_state.selected_question = None

# -------------------------------
# 사이드바 메뉴
# -------------------------------
menu_items = ["자동차 등록 현황 보기", "폐차 현황", "등록/폐차 비교", "기업 FAQ 검색"]

with st.sidebar:
    st.subheader("📂 메뉴")
    for item in menu_items:

        # 선택된 버튼 색상 변경
        if st.session_state.selected_tab == item:
            color = "#4CAF50"
            text_color = "white"
        else:
            color = "#f2f2f2"
            text_color = "black"

        if st.button(item, key=item):
            st.session_state.selected_tab = item

        st.markdown(f"""
            <style>
            div[data-baseweb="button"]:has(span:contains('{item}')) {{
                background-color: {color} !important;
                color: {text_color} !important;
            }}
            </style>
        """, unsafe_allow_html=True)

selected_tab = st.session_state.selected_tab

# -------------------------------
# 탭 1 — 자동차 등록 현황
# -------------------------------
if selected_tab == "자동차 등록 현황 보기":
    st.header("🔴 자동차 등록 현황")
    st.write("")

    years = ["2021~2025","2021","2022","2023","2024","2025"]
    regions = ["전국","서울","부산","대구","인천","광주","대전","울산","세종"]

    year = st.radio("연도 선택", years, horizontal=True)
    region = st.radio("지역 선택", regions, horizontal=True)

    if st.button("데이터 조회 등록"):
        st.info(f"{year}년 {region} 자동차 등록 현황 조회 중...")

        # 데이터 생성
        data = {
            "지역":["서울","부산","대구","인천","광주","대전","울산","세종"],
            "승용":[50000,15000,12000,10000,8000,6000,5000,2000],
            "승합":[2000,1000,800,700,500,400,300,100],
            "화물":[8000,3000,2000,1500,1200,1000,900,300],
            "특수":[300,150,100,80,60,50,40,10],
            "lat":[37.5665,35.1796,35.8714,37.4563,35.1595,36.3504,35.5384,36.4809],
            "lon":[126.9780,129.0756,128.6014,126.7052,126.8526,127.3845,129.3114,127.2890]
        }
        df = pd.DataFrame(data)

        if region != "전국":
            df = df[df["지역"] == region]

        df["총 등록대수"] = df[["승용","승합","화물","특수"]].sum(axis=1)

        st.session_state.register_data = df.copy()

        st.subheader("🔴 등록 테이블")
        st.dataframe(df)

        # 지도
        st.subheader("🔴 등록 지도")
        layer = pdk.Layer(
            "ColumnLayer",
            data=df,
            get_position='[lon, lat]',
            get_elevation='총 등록대수',
            elevation_scale=0.005,
            radius=20000,
            get_fill_color='[200,30,0,200]',
            pickable=True
        )
        view_state = pdk.ViewState(latitude=36.5, longitude=127.5, zoom=6, pitch=45)
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state,
                        tooltip={"text":"{지역}\n총 등록대수: {총 등록대수}"}))

        # 그래프
        st.subheader("🔴 등록 그래프")
        chart_data = df.set_index("지역")[["승용","승합","화물","특수"]]

        if year == "2021~2025" and region == "전국":
            long_df = chart_data.reset_index().melt(
                id_vars="지역",
                var_name="차종",
                value_name="대수"
            )
            red_colors = ["#800000","#b30000","#e60000","#ff1a1a"]

            chart = alt.Chart(long_df).mark_bar().encode(
                y="지역:N",
                x="대수:Q",
                color=alt.Color("차종:N", scale=alt.Scale(range=red_colors)),
                tooltip=["지역","차종","대수"]
            ).properties(width=700, height=400)

            st.altair_chart(chart, use_container_width=True)
        else:
            pie_data = chart_data.sum().reset_index()
            pie_data.columns = ["차종", "등록대수"]
            fig = px.pie(
                pie_data,
                names="차종",
                values="등록대수",
                color_discrete_sequence=["#b30000","#e60000","#ff1a1a","#ff6666"]
            )
            st.plotly_chart(fig)


# -------------------------------
# 탭 2 — 폐차 현황
# -------------------------------
elif selected_tab == "폐차 현황":
    st.header("🔵 자동차 폐차 현황")
    st.write("")

    years = ["2021~2025","2021","2022","2023","2024","2025"]
    regions = ["전국","서울","부산","대구","인천","광주","대전","울산","세종"]

    year = st.radio("연도 선택", years, horizontal=True, key="scrap_year")
    region = st.radio("지역 선택", regions, horizontal=True, key="scrap_region")

    if st.button("데이터 조회 폐차"):
        st.info(f"{year}년 {region} 자동차 폐차 현황 조회 중...")

        scrap = {
            "지역":["서울","부산","대구","인천","광주","대전","울산","세종"],
            "승용":[5000,1500,1200,1000,800,600,500,200],
            "승합":[200,100,80,70,50,40,30,10],
            "화물":[800,300,200,150,120,100,90,30],
            "특수":[30,15,10,8,6,5,4,1],
            "lat":[37.5665,35.1796,35.8714,37.4563,35.1595,36.3504,35.5384,36.4809],
            "lon":[126.9780,129.0756,128.6014,126.7052,126.8526,127.3845,129.3114,127.2890]
        }
        df_scrap = pd.DataFrame(scrap)

        if region != "전국":
            df_scrap = df_scrap[df_scrap["지역"] == region]

        df_scrap["총 폐차대수"] = df_scrap[["승용","승합","화물","특수"]].sum(axis=1)

        st.session_state.scrap_data = df_scrap.copy()

        st.subheader("🔵 폐차 테이블")
        st.dataframe(df_scrap)

        st.subheader("🔵 폐차 지도")
        layer = pdk.Layer(
            "ColumnLayer",
            data=df_scrap,
            get_position='[lon, lat]',
            get_elevation='총 폐차대수',
            elevation_scale=0.02,
            radius=20000,
            get_fill_color='[30,144,255,200]',
            pickable=True
        )
        view_state = pdk.ViewState(latitude=36.5, longitude=127.5, zoom=6, pitch=45)
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state,
                        tooltip={"text":"{지역}\n총 폐차대수: {총 폐차대수}"}))

        # 그래프
        st.subheader("🔵 폐차 그래프")
        chart_data = df_scrap.set_index("지역")[["승용","승합","화물","특수"]]

        if year == "2021~2025" and region == "전국":
            long_df = chart_data.reset_index().melt(
                id_vars="지역",
                var_name="차종",
                value_name="대수"
            )
            blue_colors = ["#08306b","#2171b5","#4292c6","#6baed6"]

            chart = alt.Chart(long_df).mark_bar().encode(
                y="지역:N",
                x="대수:Q",
                color=alt.Color("차종:N", scale=alt.Scale(range=blue_colors)),
                tooltip=["지역","차종","대수"]
            ).properties(width=700, height=400)

            st.altair_chart(chart, use_container_width=True)
        else:
            pie_data = chart_data.sum().reset_index()
            pie_data.columns = ["차종", "폐차대수"]
            fig = px.pie(
                pie_data,
                names="차종",
                values="폐차대수",
                color_discrete_sequence=["#3366ff","#6699ff","#99ccff","#cce0ff"]
            )
            st.plotly_chart(fig)


# ================================
# 3페이지 — 등록/폐차 비교 (버터플라이 차트)
# ================================
elif selected_tab == "등록/폐차 비교":

    st.header("🔴 자동차 등록 vs 🔵 폐차 비교")

    years = ["2021~2025","2021","2022","2023","2024","2025"]
    regions = ["전국","서울","부산","대구","인천","광주","대전","울산","세종"]

    year = st.radio("연도 선택", years, horizontal=True)
    region = st.radio("지역 선택", regions, horizontal=True)

    st.info(f"{year}년 {region} 데이터 비교")

    # ---------------------
    # 데이터 준비
    # ---------------------
    reg = {
        "지역":["서울","부산","대구","인천","광주","대전","울산","세종"],
        "승용":[50000,15000,12000,10000,8000,6000,5000,2000],
        "승합":[2000,1000,800,700,500,400,300,100],
        "화물":[8000,3000,2000,1500,1200,1000,900,300],
        "특수":[300,150,100,80,60,50,40,10]
    }
    scrap = {
        "지역":["서울","부산","대구","인천","광주","대전","울산","세종"],
        "승용":[5000,1500,1200,1000,800,600,500,200],
        "승합":[200,100,80,70,50,40,30,10],
        "화물":[800,300,200,150,120,100,90,30],
        "특수":[30,15,10,8,6,5,4,1]
    }

    df_reg = pd.DataFrame(reg)
    df_scrap = pd.DataFrame(scrap)

    if region != "전국":
        df_reg = df_reg[df_reg["지역"] == region]
        df_scrap = df_scrap[df_scrap["지역"] == region]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 등록 데이터")
        st.dataframe(df_reg)
    with col2:
        st.subheader("🔵 폐차 데이터")
        st.dataframe(df_scrap)

    red = "#e60000"
    blue = "#3366ff"

    st.subheader("🦋 버터플라이 차트")

    # ================================
    # 전국 + 전체연도 → 지역 기준 버터플라이
    # ================================
    if year == "2021~2025" and region == "전국":

        df_reg["총등록"] = df_reg[["승용","승합","화물","특수"]].sum(axis=1)
        df_scrap["총폐차"] = df_scrap[["승용","승합","화물","특수"]].sum(axis=1)

        merged = pd.merge(
            df_reg[["지역","총등록"]],
            df_scrap[["지역","총폐차"]],
            on="지역"
        )

        bf = pd.DataFrame({
            "지역": list(merged["지역"]) + list(merged["지역"]),
            "구분": ["등록"]*len(merged) + ["폐차"]*len(merged),
            "대수": list(merged["총등록"] * -1) + list(merged["총폐차"])
        })

        chart = alt.Chart(bf).mark_bar().encode(
            y="지역:N",
            x="대수:Q",
            color=alt.Color("구분:N", scale=alt.Scale(range=[red, blue])),
            tooltip=["지역","구분","대수"]
        )
        st.altair_chart(chart, use_container_width=True)

    # ================================
    # 개별 지역 선택 → 차종 기준 버터플라이(Y=차종)
    # ================================
    else:
        row_reg = df_reg.iloc[0]
        row_scrap = df_scrap.iloc[0]

        df = pd.DataFrame({
            "차종":["승용","승합","화물","특수"],
            "등록":[row_reg["승용"], row_reg["승합"], row_reg["화물"], row_reg["특수"]],
            "폐차":[-row_scrap["승용"], -row_scrap["승합"], -row_scrap["화물"], -row_scrap["특수"]],
        })

        long_df = df.melt(id_vars="차종", var_name="구분", value_name="대수")

        chart = alt.Chart(long_df).mark_bar().encode(
            y=alt.Y("차종:N", sort=["승용","승합","화물","특수"]),
            x=alt.X("대수:Q", title="대수(폐차는 음수)"),
            color=alt.Color("구분:N", scale=alt.Scale(range=[red, blue])),
            tooltip=["차종","구분","대수"]
        )
        st.altair_chart(chart, use_container_width=True)

# ================================
# 4페이지 — FAQ 검색 (중앙 정렬)
# ================================
elif selected_tab == "기업 FAQ 검색":

    st.header("🔍 FAQ 검색")

    # FAQ 데이터
    faq_data = pd.DataFrame([
        {"카테고리": "자동차 등록", "유형": "유지/환급", "단계": "초기",
        "질문": "자동차 등록은 무엇인가요?", "답변": "관할 관청에서 번호판을 발급받는 절차입니다."},
        {"카테고리": "자동차 등록", "유형": "상품/가입", "단계": "중간",
        "질문": "자동차 등록 필요 서류는?", "답변": "신분증, 자동차 구매 계약서, 보험 가입증명서 등이 필요합니다."},
        {"카테고리": "폐차", "유형": "유지/환급", "단계": "초기",
        "질문": "폐차는 어디서 하나요?", "답변": "지정 폐차장에서 가능합니다."},
        {"카테고리": "기업 FAQ", "유형": "기타", "단계": "전체",
        "질문": "회사 차량 구매 지원은?", "답변": "기업의 HR 정책에 따라 다릅니다."},
    ])

    # CSS (필터 영역/버튼 정렬)
    st.markdown("""
    <style>
    .filter-box {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 18px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }
    .filter-box > div {
        min-width: 200px;
    }
    .filter-box [data-testid="stButton"] > button {
        height: 42px;
        margin-top: 22px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 중앙 정렬 필터 UI (카테고리 제거 → 4개 필터만 사용)
    st.markdown("<div class='filter-box'>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_type = st.selectbox("유형/환급", ["전체"] + sorted(faq_data["유형"].unique()))
    with col2:
        selected_step = st.selectbox("단계", ["전체"] + sorted(faq_data["단계"].unique()))
    with col3:
        keyword = st.text_input("검색어")
    with col4:
        search_btn = st.button("조회")

    st.markdown("</div>", unsafe_allow_html=True)

    # 검색 실행
    if search_btn:
        df = faq_data.copy()

        if selected_type != "전체":
            df = df[df["유형"] == selected_type]
        if selected_step != "전체":
            df = df[df["단계"] == selected_step]
        if keyword.strip():
            df = df[df["질문"].str.contains(keyword, case=False)]

        st.subheader("조회 결과")

        if df.empty:
            st.warning("검색 결과가 없습니다.")
        else:
            for _, row in df.iterrows():
                with st.expander(f"🔸 {row['질문']}"):
                    st.markdown(f"**답변:** {row['답변']}")
    else:
        st.info("검색 조건을 선택하고 '조회' 버튼을 눌러주세요.")
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import pydeck as pdk
import plotly.express as px
import altair as alt

st.set_page_config(page_title="자동차 현황", layout="wide")

# ===============================
# CSS - 사이드바 고정 + 스타일
# ===============================
st.markdown("""
<style>
html, body {
    font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto !important;
}


button[kind="header"] { display:none !important; }
[data-testid="collapsedControl"] { display:none !important; }

/* Streamlit 최신 버전 버튼 제거 */
button[title="Collapse sidebar"],
button[title="Expand sidebar"],
div[title="Collapse sidebar"],
div[title="Expand sidebar"],
button[aria-label="Toggle sidebar"] {
    display:none !important;
}

.toggle-circle {
    position: fixed;
    top: 20px;
    left: 20px;
    width: 48px;
    height: 48px;
    background: #333;
    color: white;
    border-radius: 50%;
    font-size: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 10000;
    box-shadow: 0 3px 12px rgba(0,0,0,0.35);
    transition: 0.2s;
}
.toggle-circle:hover {
    transform: scale(1.12);
    background: black;
}

</style>
""", unsafe_allow_html=True)

# ===============================
# session_state 초기값
# ===============================
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "차량 등록 현황"

# ===============================
# 사이드바 메뉴
# ===============================
with st.sidebar:
    st.markdown("""
        <div style='font-size:22px; font-weight:700; padding:12px 8px; color:#1d1d1f;'>
            자동차 현황 시스템
        </div>

        <style>

        /* 사이드바 토글 버튼 위치 조정 */
        button[kind="header"] {
            position: fixed !important;
            left: 10px !important;     /* ★ 원하는 위치로 조정 */
            top: 15px !important;
            z-index: 99999 !important;
        }

        /* 사이드바가 접혔을 때도 동일하게 유지 */
        [data-testid="collapsedControl"] {
            position: fixed !important;
            left: 10px !important;     /* ★ 아이콘 왼쪽 끝 배치 */
            top: 15px !important;
            z-index: 99999 !important;
        }

        </style>
    """, unsafe_allow_html=True)

    selected = option_menu(
        menu_title=None,
        options=["차량 등록 현황", "폐차 현황", "등록/폐차 비교", "기업 FAQ 검색"],
        icons=["car-front", "trash", "columns-gap", "search"],
        default_index=["차량 등록 현황", "폐차 현황", "등록/폐차 비교", "기업 FAQ 검색"].index(
            st.session_state.get("selected_tab", "차량 등록 현황")
        ),
        styles={
            "container": {"background-color": "#f5f5f7", "padding": "0px"},
            "nav-link": {
                "font-size": "16px",
                "color": "#1d1d1f",
                "margin": "4px",
                "padding": "8px 12px",
                "border-radius": "10px",
                "--hover-color": "#e0e0e0",
            },
            "nav-link-selected": {
                "background-color": "#cfcfcf",
                "color": "black",
                "font-weight": "600",
            }
        },
        key="main_menu"
    )

st.session_state.selected_tab = selected
selected_tab = selected

# ===============================
# 공통 지역 데이터
# ===============================
region_list = ["서울","부산","대구","인천","광주","대전","울산","세종"]
lats = [37.5665,35.1796,35.8714,37.4563,35.1595,36.3504,35.5384,36.4809]
lons = [126.9780,129.0756,128.6014,126.7052,126.8526,127.3845,129.3114,127.2890]

# ===============================
# 등록 데이터 (연도별)
# ===============================
register_year_data = {
    "2021": {
        "승용":[40000,13000,11000,9000,7500,5500,4500,1800],
        "승합":[1800,900,700,600,400,350,250,90],
        "화물":[7000,2500,1900,1400,1100,950,850,320],
        "특수":[250,120,90,70,55,45,35,12],
    },
    "2022": {
        "승용":[42000,14000,11500,9500,7700,5800,4700,1900],
        "승합":[1850,950,720,610,420,360,260,95],
        "화물":[7200,2600,1950,1450,1150,970,860,330],
        "특수":[260,130,95,72,58,47,38,13],
    },
    "2023": {
        "승용":[45000,15000,12000,10000,8000,6000,5000,2000],
        "승합":[2000,1000,800,700,500,400,300,100],
        "화물":[8000,3000,2000,1500,1200,1000,900,300],
        "특수":[300,150,100,80,60,50,40,10],
    },
    "2024": {
        "승용":[47000,16000,12500,11000,8500,6500,5200,2200],
        "승합":[2100,1100,850,750,550,430,320,110],
        "화물":[8300,3200,2100,1600,1300,1100,920,340],
        "특수":[320,160,110,90,70,55,45,12],
    },
    "2025": {
        "승용":[50000,17000,13000,11500,9000,7000,5500,2300],
        "승합":[2200,1200,900,780,600,480,350,120],
        "화물":[8500,3400,2300,1700,1400,1200,980,360],
        "특수":[330,170,120,95,75,60,48,15],
    }
}

# ===============================
# 폐차 데이터 생성
# ===============================
def generate_scrap_data(year):
    base = {
        "승용":[6000,1800,1500,1200,900,700,600,250],
        "승합":[250,120,100,90,70,55,40,12],
        "화물":[900,350,220,160,130,110,100,35],
        "특수":[35,18,12,10,7,6,5,2]
    }

    factor = 1 - (year - 2021) * 0.02

    return pd.DataFrame({
        "지역": region_list,
        "승용":[int(v*factor) for v in base["승용"]],
        "승합":[int(v*factor) for v in base["승합"]],
        "화물":[int(v*factor) for v in base["화물"]],
        "특수":[int(v*factor) for v in base["특수"]],
        "lat": lats,
        "lon": lons
    })

# ===============================
# 폐차 합산
# ===============================
def sum_scrap_years(years):
    total = None
    for y in years:
        temp = generate_scrap_data(y)
        if total is None:
            total = temp.copy()
        else:
            total[["승용","승합","화물","특수"]] += temp[["승용","승합","화물","특수"]]
    return total


# =========================================================
# 🔴 1페이지 - 차량 등록 현황
# =========================================================
if selected_tab == "차량 등록 현황":

    st.header("🔴 차량 등록 현황")

    year = st.radio("연도 선택", ["2021~2025","2021","2022","2023","2024","2025"], horizontal=True)
    region = st.radio("지역 선택", ["전국"] + region_list, horizontal=True)

    if year == "2021~2025":
        total = None
        for y in ["2021","2022","2023","2024","2025"]:
            df_y = pd.DataFrame({
                "지역": region_list,
                "승용": register_year_data[y]["승용"],
                "승합": register_year_data[y]["승합"],
                "화물": register_year_data[y]["화물"],
                "특수": register_year_data[y]["특수"],
                "lat": lats,
                "lon": lons
            })
            if total is None:
                total = df_y.copy()
            else:
                total[["승용","승합","화물","특수"]] += df_y[["승용","승합","화물","특수"]]
        df = total.copy()
    else:
        df = pd.DataFrame({
            "지역": region_list,
            "승용": register_year_data[year]["승용"],
            "승합": register_year_data[year]["승합"],
            "화물": register_year_data[year]["화물"],
            "특수": register_year_data[year]["특수"],
            "lat": lats,
            "lon": lons
        })

    if region != "전국":
        df = df[df["지역"] == region]

    df["총 등록대수"] = df[["승용","승합","화물","특수"]].sum(axis=1)

    st.subheader("🔴 등록 테이블")
    st.dataframe(df.drop(columns=["lat", "lon"]))

    # 지도
    st.subheader("🔴 등록 지도")
    layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position='[lon, lat]',
        get_elevation="총 등록대수",
        elevation_scale=0.005,
        radius=20000,
        get_fill_color='[200,30,0,200]',
        pickable=True,
    )
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=36.5, longitude=127.5, zoom=6, pitch=45)
    ))

    # 그래프
    st.subheader("🔴 등록 그래프")
    chart_data = df.drop(columns=["lat","lon"]).set_index("지역")[["승용","승합","화물","특수"]]
    red_colors = ["#800000","#b30000","#e60000","#ff4d4d"]

    # 전국 + 전체 연도 → 바 차트
    if year == "2021~2025" and region == "전국":
        long_df = chart_data.reset_index().melt(id_vars="지역", var_name="차종", value_name="대수")

        chart = (
            alt.Chart(long_df)
            .mark_bar()
            .encode(
                y=alt.Y("지역:N", sort=["서울","부산","대구","인천","광주","대전","울산","세종"]),
                x="대수:Q",
                color=alt.Color("차종:N", scale=alt.Scale(range=red_colors))
            )
            .properties(height=450)
            .configure_axis(labelFontSize=16, titleFontSize=18)
            .configure_legend(labelFontSize=16, titleFontSize=18)
            .configure_title(fontSize=20)
        )
        st.altair_chart(chart, use_container_width=True)

    # pie 차트
    else:
        pie = chart_data.sum().reset_index()
        pie.columns = ["차종", "등록대수"]

        # 전체 합계 계산
        total = pie["등록대수"].sum()

        # ★ 라벨 문자열 만들기: "승용 / 30000 (41%)"
        pie["label_text"] = pie.apply(
            lambda row: f"{row['차종']} / {row['등록대수']} ({round(row['등록대수'] / total * 100)}%)",
            axis=1
        )

        fig = px.pie(
            pie,
            names="label_text",        # ★ 라벨 수정본 적용
            values="등록대수",
            color_discrete_sequence=red_colors
        )

        fig.update_traces(
            textinfo="label",
            textposition="outside",
            textfont_size=20,
            pull=[0.07] * len(pie),
            hovertemplate="%{label}"
        )

        fig.update_layout(
            showlegend=False,
            margin=dict(l=30, r=30, t=20, b=20)
        )

        st.plotly_chart(fig)


# =========================================================
# 🔵 2페이지 - 폐차 현황
# =========================================================
elif selected_tab == "폐차 현황":

    st.header("🔵 자동차 폐차 현황")

    year = st.radio("연도 선택", ["2021~2025","2021","2022","2023","2024","2025"], horizontal=True)
    region = st.radio("지역 선택", ["전국"] + region_list, horizontal=True)

    if year == "2021~2025":
        df = sum_scrap_years([2021,2022,2023,2024,2025])
    else:
        df = generate_scrap_data(int(year))

    if region != "전국":
        df = df[df["지역"] == region]

    df["총 폐차대수"] = df[["승용","승합","화물","특수"]].sum(axis=1)

    st.subheader("🔵 폐차 테이블")
    st.dataframe(df.drop(columns=["lat", "lon"]))

    # 지도
    st.subheader("🔵 폐차 지도")
    layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position='[lon, lat]',
        get_elevation="총 폐차대수",
        elevation_scale=0.02,
        radius=20000,
        get_fill_color='[30,144,255,200]',
        pickable=True,
    )
    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=pdk.ViewState(latitude=36.5, longitude=127.5, zoom=6, pitch=45)
        )
    )

    # 그래프
    st.subheader("🔵 폐차 그래프")
    chart_data = df.drop(columns=["lat","lon"]).set_index("지역")[["승용","승합","화물","특수"]]
    blue_colors = ["#08306b","#2171b5","#4292c6","#6baed6"]

    if year == "2021~2025" and region == "전국":
        long_df = chart_data.reset_index().melt(id_vars="지역", var_name="차종", value_name="대수")

        chart = (
            alt.Chart(long_df)
            .mark_bar()
            .encode(
                y=alt.Y("지역:N", sort=["서울","부산","대구","인천","광주","대전","울산","세종"]),
                x="대수:Q",
                color=alt.Color("차종:N", scale=alt.Scale(range=blue_colors))
            )
            .properties(height=450)
            .configure_axis(labelFontSize=16, titleFontSize=18)
            .configure_legend(labelFontSize=16, titleFontSize=18)
            .configure_title(fontSize=20)
        )


        st.altair_chart(chart, use_container_width=True)

    # pie 차트
    else:
        pie = chart_data.sum().reset_index()
        pie.columns = ["차종", "폐차대수"]

        total = pie["폐차대수"].sum()

        # ★ 라벨 수정: "화물 / 1200 (14%)"
        pie["label_text"] = pie.apply(
            lambda row: f"{row['차종']} / {row['폐차대수']} ({round(row['폐차대수'] / total * 100)}%)",
            axis=1
        )

        fig = px.pie(
            pie,
            names="label_text",
            values="폐차대수",
            color_discrete_sequence=blue_colors
        )

        fig.update_traces(
            textinfo="label",
            textposition="outside",
            textfont_size=20,
            pull=[0.07] * len(pie),
            hovertemplate="%{label}"
        )

        fig.update_layout(
            showlegend=False,
            margin=dict(l=30, r=30, t=20, b=20)
        )

        st.plotly_chart(fig)

# =========================================================
# 🟣 3페이지 - 등록/폐차 비교
# =========================================================
elif selected_tab == "등록/폐차 비교":

    st.header("🔴 자동차 등록 vs 🔵 폐차 비교")

    year = st.radio("연도 선택", ["2021~2025","2021","2022","2023","2024","2025"], horizontal=True)
    region = st.radio("지역 선택", ["전국"] + region_list, horizontal=True)

    # 🔴 등록 데이터
    if year == "2021~2025":
        reg_tot = None
        for y in ["2021","2022","2023","2024","2025"]:
            df_y = pd.DataFrame({
                "지역": region_list,
                "승용": register_year_data[y]["승용"],
                "승합": register_year_data[y]["승합"],
                "화물": register_year_data[y]["화물"],
                "특수": register_year_data[y]["특수"],
                "lat": lats,
                "lon": lons
            })
            if reg_tot is None:
                reg_tot = df_y.copy()
            else:
                reg_tot[["승용","승합","화물","특수"]] += df_y[["승용","승합","화물","특수"]]
        df_reg = reg_tot.copy()
    else:
        df_reg = pd.DataFrame({
            "지역": region_list,
            "승용": register_year_data[year]["승용"],
            "승합": register_year_data[year]["승합"],
            "화물": register_year_data[year]["화물"],
            "특수": register_year_data[year]["특수"],
            "lat": lats,
            "lon": lons
        })

    df_reg["총등록"] = df_reg[["승용","승합","화물","특수"]].sum(axis=1)

    # 🔵 폐차 데이터
    if year == "2021~2025":
        df_scrap = sum_scrap_years([2021,2022,2023,2024,2025])
    else:
        df_scrap = generate_scrap_data(int(year))

    df_scrap["총폐차"] = df_scrap[["승용","승합","화물","특수"]].sum(axis=1)

    # 지역 필터
    if region != "전국":
        df_reg = df_reg[df_reg["지역"] == region]
        df_scrap = df_scrap[df_scrap["지역"] == region]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔴 등록 데이터")
        st.dataframe(df_reg.drop(columns=["lat", "lon"]))
    with col2:
        st.subheader("🔵 폐차 데이터")
        st.dataframe(df_scrap.drop(columns=["lat", "lon"]))

    red = "#e60000"
    blue = "#3366ff"

    st.subheader("🦋 버터플라이 차트")

    # 전국 버전
    if region == "전국" and year == "2021~2025":
        merged = pd.merge(
            df_reg[["지역","총등록"]],
            df_scrap[["지역","총폐차"]],
            on="지역"
        )

        # 등록은 음수 변환 (좌측으로 보내기)
        merged["등록"] = merged["총등록"] * -1
        merged["폐차"] = merged["총폐차"]

        bf = pd.DataFrame({
            "지역": list(merged["지역"]) + list(merged["지역"]),
            "구분": ["등록"] * len(merged) + ["폐차"] * len(merged),
            "대수": list(merged["등록"]) + list(merged["폐차"])
        })

        chart = (
            alt.Chart(bf)
            .mark_bar()
            .encode(
                y=alt.Y(
                    "지역:N",
                    sort=["서울","부산","대구","인천","광주","대전","울산","세종"]   # 지역 순서 고정
                ),
                x=alt.X(
                    "대수:Q",
                    title="대수(등록=왼쪽 / 폐차=오른쪽)",
                    axis=alt.Axis(
                        labelExpr="abs(datum.value)"  # ★ 축 숫자를 절대값으로 표시!
                    )
                ),
                color=alt.Color("구분:N", scale=alt.Scale(range=[red, blue])),
                tooltip=[
                    alt.Tooltip("지역:N", title="지역"),
                    alt.Tooltip("구분:N", title="구분"),
                    alt.Tooltip("abs(대수):Q", title="대수")  # ★ tooltip도 양수!
                ]
            )
            .properties(height=450)
            .configure_axis(labelFontSize=16, titleFontSize=18)
            .configure_legend(labelFontSize=16, titleFontSize=18)
            .configure_title(fontSize=20)
        )

        st.altair_chart(chart, use_container_width=True)

    # 지역 선택 버전
    else:
        r = df_reg.iloc[0]
        s = df_scrap.iloc[0]

        df_compare = pd.DataFrame({
            "차종": ["승용","승합","화물","특수"],
            "등록": [-r["승용"], -r["승합"], -r["화물"], -r["특수"]],
            "폐차": [s["승용"], s["승합"], s["화물"], s["특수"]]
        })

        long_df = df_compare.melt(id_vars="차종", var_name="구분", value_name="대수")

        chart = (
            alt.Chart(long_df)
            .mark_bar()
            .encode(
                y=alt.Y("차종:N", sort=["승용","승합","화물","특수"]),
                x=alt.X(
                    "대수:Q",
                    title="대수(등록=왼쪽 / 폐차=오른쪽)",
                    axis=alt.Axis(
                        labelExpr="abs(datum.value)"   # ★ 축에도 양수만 보이게 함!
                    )
                ),
                color=alt.Color("구분:N", scale=alt.Scale(range=[red, blue])),
                tooltip=[
                    alt.Tooltip("차종:N", title="차종"),
                    alt.Tooltip("구분:N", title="구분"),
                    alt.Tooltip("abs(대수):Q", title="대수")  # ★ tooltip도 양수
                ]
            )
            .properties(height=450)
            .configure_axis(labelFontSize=16, titleFontSize=18)
            .configure_legend(labelFontSize=16, titleFontSize=18)
            .configure_title(fontSize=20)
        )

        st.altair_chart(chart, use_container_width=True)



elif selected_tab == "기업 FAQ 검색":

    st.header("❓ 기업 FAQ")

    # ★ 검색버튼 위치 조정 CSS 추가
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

import streamlit as st
import pydeck as pdk
import pandas as pd
import altair as alt
import plotly.express as px
import mysql.connector

# ------------------------------------------------------
# 🔵 대한민국 시도 (지역 순서 고정)
# ------------------------------------------------------
REGION_LIST = [
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남",
    "제주"
]

# ------------------------------------------------------
# 🔵 각 지역 위도/경도 (REGION_LIST와 동일 순서)
# ------------------------------------------------------
LATS = [
    37.5665, 35.1796, 35.8714, 37.4563, 35.1595, 36.3504, 35.5384, 36.4800,
    37.2636, 37.8813, 36.6424, 36.6013, 35.8242, 34.9874, 36.5684, 35.2271,
    33.4996
]

LONS = [
    126.9780, 129.0756, 128.6014, 126.7052, 126.8526, 127.3845, 129.3114, 127.2890,
    127.0286, 127.7298, 127.4890, 126.6608, 127.1470, 126.4831, 128.7294, 128.6811,
    126.5312
]


# ------------------------------------------------------
# 🔵 지역명 표준화(오탈자 방지)
# ------------------------------------------------------
REGION_ALIAS = {
    "경기도": "경기",
    "경기 ": "경기",
    "경 기": "경기",
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "총계": "전국"        # 자동 통합
}


def normalize_region(name: str):
    if not isinstance(name, str):
        return name
    name = name.strip()
    return REGION_ALIAS.get(name, name)


# ------------------------------------------------------
# 🔵 지역 → 좌표 매핑
# ------------------------------------------------------
COORD_MAP = {REGION_LIST[i]: (LATS[i], LONS[i]) for i in range(len(REGION_LIST))}


def get_coord(name):
    if name in COORD_MAP:
        return COORD_MAP[name]
    else:
        return (None, None)


# ------------------------------------------------------
# 🔵 메인 실행 함수
# ------------------------------------------------------
def run():

    # ----------------------- DB -----------------------
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="cardb"
    )

        # 승연 icon 수정 251211
    st.markdown("""
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
        """, unsafe_allow_html=True)

    st.markdown(
            """
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:20px;">
                <i class="bi-wrench-adjustable" style="font-size:50px; color:#000;"></i>
                <h1 style="margin:0; padding:0;">폐차 현황</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.write("")

    # ----------------------- UI -----------------------
    years = ["전체", "2021", "2022", "2023", "2024", "2025"]

    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT scity FROM scrapped")
    raw_regions = [normalize_region(r[0]) for r in cursor.fetchall()]

    # 중복 제거 + 오탈자 제거
    regions = [r for r in raw_regions if r in REGION_LIST]

    regions.insert(0, "전국")

    year = st.radio("연도 선택", years, horizontal=True, key="scrap_year_v2")
    region = st.radio("지역 선택", regions, horizontal=True, key="scrap_region_v2")

    # -------------------- 조회 버튼 --------------------
    if st.button("데이터 조회"):
        st.info(f"{year}년도 {region} 폐차 현황 조회 중...")

        # ------------------------------------------------------
        # 🔵 연도별 쿼리
        # ------------------------------------------------------
        if year == "전체":
            query = """
                SELECT 
                    scity,
                    SUM(CASE WHEN scar_type='승용' THEN scar_count ELSE 0 END),
                    SUM(CASE WHEN scar_type='승합' THEN scar_count ELSE 0 END),
                    SUM(CASE WHEN scar_type='화물' THEN scar_count ELSE 0 END),
                    SUM(CASE WHEN scar_type='특수' THEN scar_count ELSE 0 END),
                    SUM(stotal)
                FROM scrapped
                GROUP BY scity
            """
            cursor.execute(query)
        else:
            query = """
                SELECT 
                    scity,
                    SUM(CASE WHEN scar_type='승용' THEN scar_count ELSE 0 END),
                    SUM(CASE WHEN scar_type='승합' THEN scar_count ELSE 0 END),
                    SUM(CASE WHEN scar_type='화물' THEN scar_count ELSE 0 END),
                    SUM(CASE WHEN scar_type='특수' THEN scar_count ELSE 0 END),
                    SUM(stotal)
                FROM scrapped
                WHERE syear = %s
                GROUP BY scity
            """
            cursor.execute(query, (year,))

        result = cursor.fetchall()

        # ------------------------------------------------------
        # 🔵 DataFrame 생성
        # ------------------------------------------------------
        df = pd.DataFrame(
            result,
            columns=["지역", "승용", "승합", "화물", "특수", "전체말소수"]
        )

        df["지역"] = df["지역"].apply(normalize_region)
        df = df.apply(pd.to_numeric, errors='ignore')

        # 좌표 부여
        df["lat"] = df["지역"].apply(lambda x: get_coord(x)[0])
        df["lon"] = df["지역"].apply(lambda x: get_coord(x)[1])

        # 지도에서 사용 불가능한 지역 제외
        df = df.dropna(subset=["lat", "lon"])

        # ------------------------------------------------------
        # 🔵 전국 총계 행 추가
        # ------------------------------------------------------
        regional_df = df.copy()

        total_row = {
            "지역": "전국",
            "승용": regional_df["승용"].sum(),
            "승합": regional_df["승합"].sum(),
            "화물": regional_df["화물"].sum(),
            "특수": regional_df["특수"].sum(),
            "전체말소수": regional_df["전체말소수"].sum(),
            "lat": None,
            "lon": None
        }

        df = pd.concat([regional_df, pd.DataFrame([total_row])], ignore_index=True)

        # 기본 계산
        df["총 폐차대수"] = df[["승용", "승합", "화물", "특수"]].sum(axis=1)
        df["폐차비율(%)"] = (df["총 폐차대수"] / df["전체말소수"] * 100).round(2)

        st.session_state.scrap_data = df.copy()

        # ------------------------------------------------------
        # 🔵 지역 필터
        # ------------------------------------------------------
        if region != "전국":
            df = df[df["지역"] == region]

        # ------------------------------------------------------
        # 🔵 폐차 테이블
        # ------------------------------------------------------
        # 승연 icon 수정 251211
        st.markdown(
            """
            <h3 style="display:flex; align-items:center; gap:8px;">
                <i class="bi bi-play-fill" style="font-size:22px; color:#000;"></i>
                폐차 현황 테이블
            </h3>
            """,
            unsafe_allow_html=True
        )
        st.dataframe(df.drop(columns=["lat", "lon"]))

        # ------------------------------------------------------
        # 🔵 지도(전국 제외한 지역만 표시)
        # ------------------------------------------------------
        # 승연 icon 수정 251211
        st.markdown(
            """
            <h3 style="display:flex; align-items:center; gap:8px;">
                <i class="bi bi-play-fill" style="font-size:22px; color:#000;"></i>
                폐차 현황 지도
            </h3>
            """,
            unsafe_allow_html=True
        )
        map_df = df[df["지역"] != "전국"]

        if not map_df.empty:
            layer = pdk.Layer(
                "ColumnLayer",
                data=map_df,
                get_position='[lon, lat]',
                get_elevation='총 폐차대수',
                elevation_scale=0.02,
                radius=20000,
                get_fill_color='[30,144,255,200]',
                pickable=True
            )

            view_state = pdk.ViewState(
                latitude=36.5,
                longitude=127.5,
                zoom=6,
                pitch=45
            )

            st.pydeck_chart(
                pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip={"text": "{지역}\n총 폐차대수: {총 폐차대수}"}
                )
            )

        # ------------------------------------------------------
        # 🔵 그래프
        # ------------------------------------------------------
        # 승연 icon 수정 251211
        st.markdown(
            """
            <h3 style="display:flex; align-items:center; gap:8px;">
                <i class="bi bi-play-fill" style="font-size:22px; color:#000;"></i>
                폐차 현황 그래프
            </h3>
            """,
            unsafe_allow_html=True
        )

        chart_df = df.drop(columns=["lat", "lon"]).set_index("지역")[["승용", "승합", "화물", "특수"]]

        colors = ["#08306b", "#2171b5", "#4292c6", "#6baed6"]

        # 전체 + 전국 → 막대 그래프
        if year == "전체" and region == "전국":

            long_df = chart_df.reset_index().melt(
                id_vars="지역",
                var_name="차종",
                value_name="대수"
            )

            bar_chart = (
                alt.Chart(long_df)
                .mark_bar()
                .encode(
                    y=alt.Y("지역:N", sort=None),
                    x="대수:Q",
                    color=alt.Color("차종:N", scale=alt.Scale(range=colors)),
                    tooltip=["지역", "차종", "대수"]
                )
                .properties(width=700, height=450)
            )

            st.altair_chart(bar_chart, use_container_width=True)

        # 그 외 → 파이 차트
        else:
            pie_data = chart_df.sum().reset_index()
            pie_data.columns = ["차종", "대수"]

            total = pie_data["대수"].sum()

            pie_data["label"] = pie_data.apply(
                lambda r: f"{r['차종']} / {r['대수']} ({round(r['대수']/total*100)}%)",
                axis=1
            )

            fig = px.pie(
                pie_data,
                names="label",
                values="대수",
                color_discrete_sequence=colors
            )

            fig.update_traces(
                textinfo="label",
                textposition="outside",
                pull=[0.07] * len(pie_data)
            )

            st.plotly_chart(fig)

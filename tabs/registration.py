import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
import plotly.express as px
import mysql.connector

def run():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="cardb"
    )

    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT rcity FROM registered")
    regions = [row[0] for row in cursor.fetchall()]

    # ⭐ "총계" → "전국"
    regions = ["전국" if r == "총계" else r for r in regions]

    # ⭐ 중복 제거 + 전국 맨 앞으로
    regions = list(regions)
    if "전국" in regions:
        regions.remove("전국")
    regions.insert(0, "전국")

    st.header("🔴 자동차 등록 현황")
    st.write("")

    years = ["전체", "2021", "2022", "2023", "2024", "2025"]
    year = st.radio("연도 선택", years, horizontal=True)
    region = st.radio("지역 선택", regions, horizontal=True)

    if st.button("데이터 조회"):
        st.info(f"{year}년 {region} 자동차 등록 현황 조회 중...")

        if year == "전체":
            query = """
                SELECT 
                    rcity,
                    SUM(CASE WHEN rcar_type='승용' THEN rcar_count ELSE 0 END),
                    SUM(CASE WHEN rcar_type='승합' THEN rcar_count ELSE 0 END),
                    SUM(CASE WHEN rcar_type='화물' THEN rcar_count ELSE 0 END),
                    SUM(CASE WHEN rcar_type='특수' THEN rcar_count ELSE 0 END)
                FROM registered
                GROUP BY rcity
            """
            cursor.execute(query)

        else:
            query = """
                SELECT 
                    rcity,
                    SUM(CASE WHEN rcar_type='승용' THEN rcar_count ELSE 0 END),
                    SUM(CASE WHEN rcar_type='승합' THEN rcar_count ELSE 0 END),
                    SUM(CASE WHEN rcar_type='화물' THEN rcar_count ELSE 0 END),
                    SUM(CASE WHEN rcar_type='특수' THEN rcar_count ELSE 0 END)
                FROM registered
                WHERE ryear = %s
                GROUP BY rcity
            """
            cursor.execute(query, (year,))

        result = cursor.fetchall()

        df = pd.DataFrame(result, columns=["지역", "승용", "승합", "화물", "특수"])

        # ⭐ 여기서도 "총계" → "전국"
        df["지역"] = df["지역"].apply(lambda x: "전국" if x == "총계" else x)

        df = df.apply(pd.to_numeric, errors='ignore')

        # 좌표 매핑
        region_coords = {
            "서울": (37.5665, 126.9780),
            "부산": (35.1796, 129.0756),
            "대구": (35.8714, 128.6014),
            "인천": (37.4563, 126.7052),
            "광주": (35.1595, 126.8526),
            "대전": (36.3504, 127.3845),
            "울산": (35.5384, 129.3114),
            "세종": (36.4800, 127.2890),
            "경기": (37.2636, 127.0286),
            "강원": (37.8813, 127.7298),
            "충북": (36.6424, 127.4890),
            "충남": (36.6013, 126.6608),
            "전북": (35.8242, 127.1470),
            "전남": (34.9874, 126.4831),
            "경북": (36.5684, 128.7294),
            "경남": (35.2271, 128.6811),
            "제주": (33.4996, 126.5312),
        }

        coord_df = pd.DataFrame(
            [{"지역": key, "lat": v[0], "lon": v[1]} for key, v in region_coords.items()]
        )

        df = df.merge(coord_df, on="지역", how="left")

        if region != "전국":
            df = df[df["지역"] == region]

        df["총 등록대수"] = df[["승용", "승합", "화물", "특수"]].sum(axis=1)

        # 테이블 출력
        st.subheader("🔴 등록 테이블")
        st.dataframe(df.drop(columns=["lat", "lon"]))

        # 지도 출력
        st.subheader("🔴 등록 지도")

        layer = pdk.Layer(
            "ColumnLayer",
            data=df,
            get_position='[lon, lat]',
            get_elevation='총 등록대수',
            elevation_scale=0.005,
            radius=20000,
            get_fill_color=[200, 30, 0, 200],
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
                tooltip={"text": "{지역}\n총 등록대수: {총 등록대수}"}
            )
        )

        # 그래프 출력
        st.subheader("🔴 등록 그래프")

        chart_data = df.drop(columns=["lat", "lon"]).set_index("지역")[["승용", "승합", "화물", "특수"]]

        red_colors = ["#800000", "#b30000", "#e60000", "#ff4d4d"]

        # 전국 + 전체 → 막대그래프
        if year == "전체" and region == "전국":
            long_df = chart_data.reset_index().melt(
                id_vars="지역", var_name="차종", value_name="대수"
            )

            bar_chart = (
                alt.Chart(long_df)
                .mark_bar()
                .encode(
                    y=alt.Y("지역:N", sort=None),
                    x="대수:Q",
                    color=alt.Color("차종:N", scale=alt.Scale(range=red_colors)),
                    tooltip=["지역", "차종", "대수"]
                )
            )

            st.altair_chart(bar_chart, use_container_width=True)

        # 나머지 → 파이차트
        # 나머지 → 파이차트
        else:
            pie_data = chart_data.sum().reset_index()
            pie_data.columns = ["차종", "등록대수"]
            total = pie_data["등록대수"].sum()

            # ⭐ 2페이지와 동일한 형식의 레이블
            pie_data["label"] = pie_data.apply(
                lambda r: f"{r['차종']} / {r['등록대수']} ({round(r['등록대수'] / total * 100, 2)}%)"
                if total != 0
                else f"{r['차종']} / 0 (0%)",
                axis=1
            )

            fig = px.pie(
                pie_data,
                names="label",
                values="등록대수",
                color_discrete_sequence=red_colors
            )

            fig.update_traces(
                textinfo="label",
                textposition="outside",
                pull=[0.07] * len(pie_data)
            )

            st.plotly_chart(fig)

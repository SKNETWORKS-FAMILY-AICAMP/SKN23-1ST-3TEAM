import streamlit as st
import pydeck as pdk
import pandas as pd
import altair as alt
import plotly.express as px
import mysql.connector
from data import REGION_LIST, generate_scrap_data, sum_scrap_years

def run():
        connection = mysql.connector.connect(
        host = "localhost",         # MySQL 서버 주소
        user = "root",              # 사용자 이름
        password = "1234",          # 비밀번호
        database = "cardb"    # 사용할 데이터베이스
    )
        
        st.header("🔵 자동차 폐차 현황")
        st.write("")

        # 연도 / 지역 선택 UI
        years = ["2021~2025", "2021", "2022", "2023", "2024", "2025"]

        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT scity FROM scrapped")
        regions = [row[0] for row in cursor.fetchall()]

        year = st.radio("연도 선택", years, horizontal=True, key="scrap_year")
        region = st.radio("지역 선택", regions, horizontal=True, key="scrap_region")

        if st.button("데이터 조회 폐차"):
            st.info(f"{year}년 {region} 자동차 폐차 현황 조회 중...")

            # --------------------------------------------------
            # 🔵 연도 선택에 따른 쿼리 변경 (등록 코드와 동일 로직)
            # --------------------------------------------------
            if year == "2021~2025":
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

            # --------------------------------------------------
            # 🔵 DataFrame 구성 (등록 코드 스타일로 동일하게)
            # --------------------------------------------------
            df_scrap = pd.DataFrame(result, columns=["지역","승용","승합","화물","특수","전체말소수"])
            df_scrap = df_scrap.apply(pd.to_numeric, errors='ignore')
        
            # --------------------------------------------------
            # 🔵 위도/경도는 code1과 동일한 방식으로 분리하여 적용
            # --------------------------------------------------
            lats = [
                37.5665, 35.1796, 35.8714, 37.4563, 35.1595, 36.3504, 35.5384, 36.4800,
                37.2636, 37.8813, 36.6424, 36.6013, 35.8242, 34.9874, 36.5684, 35.2271,
                33.4996, 37.5665
            ]
            lons = [
                126.9780, 129.0756, 128.6014, 126.7052, 126.8526, 127.3845, 129.3114, 127.2890,
                127.0286, 127.7298, 127.4890, 126.6608, 127.1470, 126.4831, 128.7294, 128.6811,
                126.5312, 126.9780
            ]

            # DF 길이에 맞게 좌표 할당
            df_scrap["lat"] = lats[:len(df_scrap)]
            df_scrap["lon"] = lons[:len(df_scrap)]
            df_scrap["lat"] = df_scrap["lat"].astype(float)
            df_scrap["lon"] = df_scrap["lon"].astype(float)

            # 지역 필터 (등록 코드와 동일)
            if region != "총계":
                df_scrap = df_scrap[df_scrap["지역"] == region]

            # 총 폐차대수 계산
            df_scrap["총 폐차대수"] = df_scrap[["승용","승합","화물","특수"]].sum(axis=1)
            df_scrap["폐차비율(%)"] = (df_scrap["총 폐차대수"] / df_scrap["전체말소수"] * 100).round(2)
            st.session_state.scrap_data = df_scrap.copy()

            # --------------------------------------------------
            # 🔵 폐차 테이블 (위도/경도는 숨김)
            # --------------------------------------------------
            st.subheader("🔵 폐차 테이블")
            st.dataframe(df_scrap.drop(columns=["lat","lon"]))

            # --------------------------------------------------
            # 🔵 폐차 지도 (pydeck ColumnLayer)
            # --------------------------------------------------
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
                    tooltip={"text":"{지역}\n총 폐차대수: {총 폐차대수}"}
                )
            )

        # --------------------------------------------------
            # 🔵 폐차 그래프 (등록 코드와 동일한 구조)
            # --------------------------------------------------
            st.subheader("🔵 폐차 그래프")

            # lat/lon 제거 후 그래프용 DF 구성
            chart_data = df_scrap.drop(columns=["lat", "lon"]).set_index("지역")[["승용","승합","화물","특수"]]

            blue_colors = ["#08306b","#2171b5","#4292c6","#6baed6"]

            # --------------------------------------------------
            # 🔵 1) 2021~2025 + 총계 → 막대 그래프
            # --------------------------------------------------
            if year == "2021~2025" and region == "총계":

                long_df = chart_data.reset_index().melt(
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
                        color=alt.Color("차종:N", scale=alt.Scale(range=blue_colors)),
                        tooltip=["지역", "차종", "대수"]
                    )
                    .properties(width=700, height=450)
                    .configure_axis(labelFontSize=14, titleFontSize=16)
                    .configure_legend(labelFontSize=14, titleFontSize=16)
                )

                st.altair_chart(bar_chart, use_container_width=True)

            # --------------------------------------------------
            # 🔵 2) 그 외 → 파이 차트
            # --------------------------------------------------
            else:
                pie_data = chart_data.sum().reset_index()
                pie_data.columns = ["차종", "폐차대수"]

                total = pie_data["폐차대수"].sum()

                # 라벨 포맷: "승용 / 30000 (41%)"
                pie_data["label"] = pie_data.apply(
                    lambda r: f"{r['차종']} / {r['폐차대수']} ({round(r['폐차대수']/total*100)}%)",
                    axis=1
                )

                fig = px.pie(
                    pie_data,
                    names="label",
                    values="폐차대수",
                    color_discrete_sequence=blue_colors
                )

                fig.update_traces(
                    textinfo="label",
                    textposition="outside",
                    textfont_size=18,
                    pull=[0.07] * len(pie_data),
                    hovertemplate="%{label}"
                )

                fig.update_layout(
                    showlegend=False,
                    margin=dict(l=20, r=20, t=10, b=10)
                )

                st.plotly_chart(fig)


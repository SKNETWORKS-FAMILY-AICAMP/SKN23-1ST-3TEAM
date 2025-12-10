import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
import plotly.express as px
import mysql.connector
from data import REGION_LIST, LATS, LONS, REGISTER_YEAR_DATA

def run():
    connection = mysql.connector.connect(
        host = "localhost",         # MySQL 서버 주소
        user = "root",              # 사용자 이름
        password = "1234",          # 비밀번호
        database = "cardb"    # 사용할 데이터베이스
    )

    # ---------------------------
    # 🔴 DB에서 지역 리스트 가져오기
    # ---------------------------
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT rcity FROM registered")
    regions = [row[0] for row in cursor.fetchall()]

    # --------------------------------------------------
    # 🔴 Streamlit UI
    # --------------------------------------------------

    st.header("🔴 자동차 등록 현황")
    st.write("")

    years = ["2021~2025", "2021", "2022", "2023", "2024", "2025"]
    
    year = st.radio("연도 선택", years, horizontal=True)
    region = st.radio("지역 선택", regions, horizontal=True)

    if st.button("데이터 조회 등록"):
        st.info(f"{year}년 {region} 자동차 등록 현황 조회 중...")

        # --------------------------------------------------
        # 🔴 만약 사용자가 “2021~2025”를 선택하면 — 전체 연도 합계 처리
        # --------------------------------------------------
        if year == "2021~2025":
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
        
        # --------------------------------------------------
        # 🔴 특정 연도 선택 시 — 해당 연도만 조회
        # --------------------------------------------------
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

        # --------------------------------------------------
        # 🔴 DataFrame 구성
        # --------------------------------------------------
    # (중략) result = cursor.fetchall() 이후부터 수정된 부분

        df = pd.DataFrame(result, columns=["지역","승용","승합","화물","특수"])
        df = df.apply(pd.to_numeric, errors='ignore')

        # 위도/경도 리스트는 기존대로
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

        # df의 지역 순서에 맞게 좌표 넣기 (길이 맞추기 위해 슬라이스)
        df["lat"] = lats[:len(df)]
        df["lon"] = lons[:len(df)]

        # 숫자 타입으로 안전하게 캐스팅
        df["lat"] = df["lat"].astype(float)
        df["lon"] = df["lon"].astype(float)

        # 지역 필터 적용 (네 코드에선 "총계"인지 "전국"인지 확인)
        if region != "총계":
            df = df[df["지역"] == region]

        df["총 등록대수"] = df[["승용","승합","화물","특수"]].sum(axis=1)

        st.session_state.register_data = df.copy()

        st.subheader("🔴 등록 테이블")
        st.dataframe(df.drop(columns=["lat","lon"]))  # 테이블엔 좌표 숨기기 원하면 이렇게

        # 지도
        st.subheader("🔴 등록 지도")
        layer = pdk.Layer(
            "ColumnLayer",
            data=df,
            # ← 여기가 중요: 문자열 accessor, 경도(lon) 먼저, 위도(lat) 나중
            get_position='[lon, lat]',
            get_elevation='총 등록대수',
            elevation_scale=0.005,
            radius=20000,
            get_fill_color=[200, 30, 0, 200],
            pickable=True
        )

        view_state = pdk.ViewState(latitude=36.5, longitude=127.5, zoom=6, pitch=45)

        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text":"{지역}\n총 등록대수: {총 등록대수}"}
            )
        )

        # --------------------------------------------------
        # 🔴 등록 그래프
        # --------------------------------------------------
        st.subheader("🔴 등록 그래프")

        # lat/lon 없는 DataFrame 사용
        chart_data = df.drop(columns=["lat", "lon"]).set_index("지역")[["승용","승합","화물","특수"]]

        # 빨간 계열 색상
        red_colors = ["#800000","#b30000","#e60000","#ff4d4d"]

        # --------------------------------------------------
        # 🔴 1) 2021~2025 + 총계 → 막대 그래프
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
                    y=alt.Y("지역:N", sort = None),
                    x="대수:Q",
                    color=alt.Color("차종:N", scale=alt.Scale(range=red_colors)),
                    tooltip=["지역", "차종", "대수"]
                )
                .properties(width=700, height=450)
                .configure_axis(labelFontSize=14, titleFontSize=16)
                .configure_legend(labelFontSize=14, titleFontSize=16)
            )

            st.altair_chart(bar_chart, use_container_width=True)

        # --------------------------------------------------
        # 🔴 2) 그 외 모든 경우 → 파이 차트
        # --------------------------------------------------
        else:
            pie_data = chart_data.sum().reset_index()
            pie_data.columns = ["차종", "등록대수"]

            total = pie_data["등록대수"].sum()

            # 라벨 예시: "승용 / 30000 (41%)"
            pie_data["label"] = pie_data.apply(
                lambda r: f"{r['차종']} / {r['등록대수']} ({round(r['등록대수']/total*100)}%)",
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
                textfont_size=18,
                pull=[0.07] * len(pie_data),
                hovertemplate="%{label}"
            )

            fig.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=10, b=10)
            )

            st.plotly_chart(fig)




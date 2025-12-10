import streamlit as st
import pydeck as pdk
import altair as alt
import plotly.express as px
from data import REGION_LIST, generate_scrap_data, sum_scrap_years

def run():
    st.header("🔵 자동차 폐차 현황")

    year = st.radio("연도 선택", ["2021~2025","2021","2022","2023","2024","2025"], horizontal=True, key="scrap_year")
    region = st.radio("지역 선택", ["전국"] + REGION_LIST, horizontal=True, key="scrap_region")

    if year == "2021~2025":
        df = sum_scrap_years([2021,2022,2023,2024,2025])
    else:
        df = generate_scrap_data(int(year))

    if region != "전국":
        df = df[df["지역"] == region]

    df["총 폐차대수"] = df[["승용","승합","화물","특수"]].sum(axis=1)

    st.subheader("🔵 폐차 테이블")
    st.dataframe(df.drop(columns=["lat", "lon"]))

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

    st.subheader("🔵 폐차 그래프")
    chart_data = df.drop(columns=["lat","lon"]).set_index("지역")[["승용","승합","화물","특수"]]
    blue_colors = ["#08306b","#2171b5","#4292c6","#6baed6"]

    if year == "2021~2025" and region == "전국":
        long_df = chart_data.reset_index().melt(id_vars="지역", var_name="차종", value_name="대수")
        chart = (
            alt.Chart(long_df)
            .mark_bar()
            .encode(
                y=alt.Y("지역:N", sort=REGION_LIST),
                x="대수:Q",
                color=alt.Color("차종:N", scale=alt.Scale(range=blue_colors))
            )
            .properties(height=450)
            .configure_axis(labelFontSize=16, titleFontSize=18)
            .configure_legend(labelFontSize=16, titleFontSize=18)
            .configure_title(fontSize=20)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        pie = chart_data.sum().reset_index()
        pie.columns = ["차종", "폐차대수"]
        total_val = pie["폐차대수"].sum()
        pie["label_text"] = pie.apply(
            lambda row: f"{row['차종']} / {row['폐차대수']} ({round(row['폐차대수'] / total_val * 100)}%)",
            axis=1
        )
        fig = px.pie(pie, names="label_text", values="폐차대수", color_discrete_sequence=blue_colors)
        fig.update_traces(textinfo="label", textposition="outside", textfont_size=20, pull=[0.07] * len(pie), hovertemplate="%{label}")
        fig.update_layout(showlegend=False, margin=dict(l=30, r=30, t=20, b=20))
        st.plotly_chart(fig)
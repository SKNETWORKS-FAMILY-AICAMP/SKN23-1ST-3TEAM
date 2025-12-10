import streamlit as st
import pandas as pd
import altair as alt
from data import REGION_LIST, LATS, LONS, REGISTER_YEAR_DATA, generate_scrap_data, sum_scrap_years

def run():
    st.header("🔴 자동차 등록 vs 🔵 폐차 비교")

    year = st.radio("연도 선택", ["2021~2025","2021","2022","2023","2024","2025"], horizontal=True, key="comp_year")
    region = st.radio("지역 선택", ["전국"] + REGION_LIST, horizontal=True, key="comp_region")

    # 🔴 등록 데이터
    if year == "2021~2025":
        reg_tot = None
        for y in ["2021","2022","2023","2024","2025"]:
            df_y = pd.DataFrame({
                "지역": REGION_LIST,
                "승용": REGISTER_YEAR_DATA[y]["승용"],
                "승합": REGISTER_YEAR_DATA[y]["승합"],
                "화물": REGISTER_YEAR_DATA[y]["화물"],
                "특수": REGISTER_YEAR_DATA[y]["특수"],
                "lat": LATS,
                "lon": LONS
            })
            if reg_tot is None:
                reg_tot = df_y.copy()
            else:
                reg_tot[["승용","승합","화물","특수"]] += df_y[["승용","승합","화물","특수"]]
        df_reg = reg_tot.copy()
    else:
        df_reg = pd.DataFrame({
            "지역": REGION_LIST,
            "승용": REGISTER_YEAR_DATA[year]["승용"],
            "승합": REGISTER_YEAR_DATA[year]["승합"],
            "화물": REGISTER_YEAR_DATA[year]["화물"],
            "특수": REGISTER_YEAR_DATA[year]["특수"],
            "lat": LATS,
            "lon": LONS
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

    if region == "전국" and year == "2021~2025":
        merged = pd.merge(df_reg[["지역","총등록"]], df_scrap[["지역","총폐차"]], on="지역")
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
                y=alt.Y("지역:N", sort=REGION_LIST),
                x=alt.X("대수:Q", title="대수(등록=왼쪽 / 폐차=오른쪽)", axis=alt.Axis(labelExpr="abs(datum.value)")),
                color=alt.Color("구분:N", scale=alt.Scale(range=[red, blue])),
                tooltip=[
                    alt.Tooltip("지역:N", title="지역"),
                    alt.Tooltip("구분:N", title="구분"),
                    alt.Tooltip("abs(대수):Q", title="대수")
                ]
            )
            .properties(height=450)
            .configure_axis(labelFontSize=16, titleFontSize=18)
            .configure_legend(labelFontSize=16, titleFontSize=18)
            .configure_title(fontSize=20)
        )
        st.altair_chart(chart, use_container_width=True)

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
                x=alt.X("대수:Q", title="대수(등록=왼쪽 / 폐차=오른쪽)", axis=alt.Axis(labelExpr="abs(datum.value)")),
                color=alt.Color("구분:N", scale=alt.Scale(range=[red, blue])),
                tooltip=[
                    alt.Tooltip("차종:N", title="차종"),
                    alt.Tooltip("구분:N", title="구분"),
                    alt.Tooltip("abs(대수):Q", title="대수")
                ]
            )
            .properties(height=450)
            .configure_axis(labelFontSize=16, titleFontSize=18)
            .configure_legend(labelFontSize=16, titleFontSize=18)
            .configure_title(fontSize=20)
        )
        st.altair_chart(chart, use_container_width=True)
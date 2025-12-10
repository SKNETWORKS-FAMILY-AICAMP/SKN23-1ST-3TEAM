import mysql.connector
import pandas as pd
import altair as alt
import streamlit as st

# 이 코드가 하는 전체 일
    # 1. MySQL(DB)에서 registered(등록) / scrapped(폐차) 데이터를 가져온다.
    # 2. 연도(2021~2025, 전체)와 지역(전국 + 시도)을 선택하는 UI를 만든다.
    # 3. 선택한 조건에 맞게:
    #   * 등록/폐차 테이블을 합쳐서
    #   * “승용(등록)/승용(폐차)” 같이 한 표에 보여주고,
    #   * 등록은 빨간색, 폐차는 파란색으로 구분해서 스타일링한다.
    # 4. 같은 데이터를 이용해서 Altair로 버터플라이 차트 (왼쪽 등록, 오른쪽 폐차)를 그린다.
    #   * 전국 + 전체 → 지역별 등록 vs 폐차
    #   * 그 외 → 차종별 등록 vs 폐차

# main.py에서 이 페이지를 실행할 때 호출할 메인 함수
def run():
    st.header("🔴 자동차 등록 · 🔵 폐차 비교 현황")

    years = ["전체", "2021", "2022", "2023", "2024", "2025"]

    # ---------------------------
    # 1) DB 연결 & 지역 리스트 읽기
    # ---------------------------
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="cardb"
    )
    cursor = connection.cursor()

    # 등록 테이블 지역
    # 등록 테이블에서 rcity(등록 지역)값들을 중복없이 가져옴
    cursor.execute("SELECT DISTINCT rcity FROM registered")
    # 등록 데이터에 등장하는 지역 이름 리스트를 fetchall을 이용해서 한번에 가져옴
    reg_regions = [row[0] for row in cursor.fetchall()]

    # 폐차 테이블 지역
    cursor.execute("SELECT DISTINCT scity FROM scrapped")
    scrap_regions = [row[0] for row in cursor.fetchall()]

    # 두 테이블 모두에 존재하는 지역 기준 (총계/합계 행은 제외)
    # 두 리스트의 합집합(중복 제거)
    regions = sorted(set(reg_regions) | set(scrap_regions))
    # 총계는 실제 지역이 아니니 제외하고 실제 지역 목록
    regions = [r for r in regions if r not in ("총계",)]

    # ---------------------------
    # 2) 연도 / 지역 선택 UI
    # ---------------------------
    # 제목을 HTML + CSS로 따로 출력
    st.markdown(
        "<div style='font-size:20px; font-weight:700; margin-bottom:-50px'>연도 선택</div>",
        unsafe_allow_html=True
    )
    year = st.radio(
        label="",        # 라벨은 비워두기
        options=years,   # 전체,2021... 중 선택
        horizontal=True, # 가로로 나열
        key="comp_year"
    )
    
    st.markdown(
        "<div style='font-size:20px; font-weight:700; margin-bottom: -20px'>지역 선택</div>",
        unsafe_allow_html=True
    )
    region = st.radio(
        label="",                # 라벨은 비워두기
        options=["전국"] + regions,
        horizontal=True,
        key="comp_region"
    )

    # ---------------------------
    # 3) 등록/폐차 데이터 조회 함수
    # ---------------------------
    # selected_year를 받아 registered 테이블에서 지역별 합계를 가져오는 함수
    def get_register_df(selected_year: str) -> pd.DataFrame:
        """registered 테이블에서 연도 조건에 맞는 지역별 합계 가져오기"""
        # 연도가 전체이면 where 조건없이 전체 연도에 대해 각 지역별로 차종의 합계를 계산
        if selected_year == "전체":
            query = """
                SELECT 
                    rcity,
                    SUM(CASE WHEN rcar_type='승용' THEN rcar_count ELSE 0 END) AS 승용,
                    SUM(CASE WHEN rcar_type='승합' THEN rcar_count ELSE 0 END) AS 승합,
                    SUM(CASE WHEN rcar_type='화물' THEN rcar_count ELSE 0 END) AS 화물,
                    SUM(CASE WHEN rcar_type='특수' THEN rcar_count ELSE 0 END) AS 특수
                FROM registered
                GROUP BY rcity
            """
            cursor.execute(query)
        else:
        # 특정 연도를 선택한 경우 where %s 조건으로 해당 연도만 필터
            query = """
                SELECT 
                    rcity,
                    SUM(CASE WHEN rcar_type='승용' THEN rcar_count ELSE 0 END) AS 승용,
                    SUM(CASE WHEN rcar_type='승합' THEN rcar_count ELSE 0 END) AS 승합,
                    SUM(CASE WHEN rcar_type='화물' THEN rcar_count ELSE 0 END) AS 화물,
                    SUM(CASE WHEN rcar_type='특수' THEN rcar_count ELSE 0 END) AS 특수
                FROM registered
                WHERE ryear = %s
                GROUP BY rcity
            """
            # 파라미터 바인딩으로 sql 인젝션을 방지+타입 처리
            cursor.execute(query, (selected_year,))

        # sql 결과를 모두 가져와 rows에 저장
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=["지역", "승용", "승합", "화물", "특수"])
        # 숫자형으로 캐스팅
        for c in ["승용", "승합", "화물", "특수"]:
            # numeric : 숫자 아닌 값은 NaN / fillna : NaN은 0 / .astype(int) : 최종 int형
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
        # 최종적으로 지역별 등록 대수를 dataframe으로 반환
        return df

    def get_scrap_df(selected_year: str) -> pd.DataFrame:
        """scrapped 테이블에서 연도 조건에 맞는 지역별 합계 가져오기"""
        if selected_year == "전체":
            query = """
                SELECT 
                    scity,
                    SUM(CASE WHEN scar_type='승용' THEN scar_count ELSE 0 END) AS 승용,
                    SUM(CASE WHEN scar_type='승합' THEN scar_count ELSE 0 END) AS 승합,
                    SUM(CASE WHEN scar_type='화물' THEN scar_count ELSE 0 END) AS 화물,
                    SUM(CASE WHEN scar_type='특수' THEN scar_count ELSE 0 END) AS 특수
                FROM scrapped
                GROUP BY scity
            """
            cursor.execute(query)
        else:
            query = """
                SELECT 
                    scity,
                    SUM(CASE WHEN scar_type='승용' THEN scar_count ELSE 0 END) AS 승용,
                    SUM(CASE WHEN scar_type='승합' THEN scar_count ELSE 0 END) AS 승합,
                    SUM(CASE WHEN scar_type='화물' THEN scar_count ELSE 0 END) AS 화물,
                    SUM(CASE WHEN scar_type='특수' THEN scar_count ELSE 0 END) AS 특수
                FROM scrapped
                WHERE syear = %s
                GROUP BY scity
            """
            cursor.execute(query, (selected_year,))

        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=["지역", "승용", "승합", "화물", "특수"])
        # 숫자형으로 캐스팅
        for c in ["승용", "승합", "화물", "특수"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
        return df

    # ---------------------------
    # 4) 실제 데이터 조회
    # ---------------------------
    # year기준으로 등록/폐차 데이터 조회
    df_reg = get_register_df(year)
    df_scrap = get_scrap_df(year)

    # 다시한번 지역이 regions목록에 포함된 행만 남김(insn은 일치여부 반환)
    # 혹시 db에 '총계' 같은 행이 있어도 제거
    df_reg = df_reg[df_reg["지역"].isin(regions)]
    df_scrap = df_scrap[df_scrap["지역"].isin(regions)]

    # 선택 지역 필터링
    # 특정 지역을 선택한 경우 -> 해당 지역만 남기고 나머지 지역 행은 제거
    if region != "전국":
        df_reg = df_reg[df_reg["지역"] == region]
        df_scrap = df_scrap[df_scrap["지역"] == region]
    else:
        # 전국 + 개별연도(전체가 아닌 경우) → 모든 지역 합쳐서 1행으로
        if year != "전체":
            reg_sum = df_reg[["승용", "승합", "화물", "특수"]].sum()
            df_reg = pd.DataFrame(
                [["전국"] + list(reg_sum)],
                columns=["지역", "승용", "승합", "화물", "특수"]
            )

            scrap_sum = df_scrap[["승용", "승합", "화물", "특수"]].sum()
            df_scrap = pd.DataFrame(
                [["전국"] + list(scrap_sum)],
                columns=["지역", "승용", "승합", "화물", "특수"]
            )
    # 위 코드 외 전국 + 전체(연도)인 경우 위에서 합치지 않고 각 지역별 행에 그대로 유지
    # 버터플라이 차트에서 지역을 여러줄로 보여주기 위해

    # 각 행(지역 혹은 전국)에 대해 총 등록/폐차 대수 컬럼 추가
    df_reg["총등록"] = df_reg[["승용", "승합", "화물", "특수"]].sum(axis=1)
    df_scrap["총폐차"] = df_scrap[["승용", "승합", "화물", "특수"]].sum(axis=1)

    # ---------------------------
    # 5) 테이블 출력 전 전처리
    # ---------------------------
    # lat/lon 들어있는 경우 제거
    # 테이블에 위도/경도가 있다면 필요없으므로 삭제
    if "lat" in df_reg.columns:
        df_reg = df_reg.drop(columns=["lat", "lon"])
    if "lat" in df_scrap.columns:
        df_scrap = df_scrap.drop(columns=["lat", "lon"])

    # ---------------------------
    # 🔗 등록 / 폐차 머지 (이전 코드와 동일)
    # ---------------------------
    df_reg_ren = df_reg.rename(columns={
        "승용": "승용_등록",
        "승합": "승합_등록",
        "화물": "화물_등록",
        "특수": "특수_등록",
        "총등록": "총등록"
    })

    df_scrap_ren = df_scrap.rename(columns={
        "승용": "승용_폐차",
        "승합": "승합_폐차",
        "화물": "화물_폐차",
        "특수": "특수_폐차",
        "총폐차": "총폐차"
    })

    # 지역을 기준으로 등록/폐차의 dataframe을 합침
    # 한 행에 등록+폐차 데이터가 모두 들어옴
    merged = pd.merge(df_reg_ren, df_scrap_ren, on="지역", how="inner")

    # 👉 컬럼 순서: 차종별로 (등록, 폐차) 묶음
    merged = merged[
        [
            "지역",
            "승용_등록", "승용_폐차",
            "승합_등록", "승합_폐차",
            "화물_등록", "화물_폐차",
            "특수_등록", "특수_폐차",
            "총등록", "총폐차",
        ]
    ]
    # --------------------------------------------------
    # 🧮 2021~2025 + 전국 선택 시, '전국' 합계 행을 맨 위에 추가
    # --------------------------------------------------
    if year == "전체" and region == "전국":
        total_row = {"지역": "전국"}

        # '지역'을 제외한 나머지 숫자 컬럼들의 합산
        for col in merged.columns[1:]:
            total_row[col] = merged[col].sum()

        # 전국 합계 행을 맨 위에 붙이기
        merged = pd.concat(
            [pd.DataFrame([total_row]), merged],
            ignore_index=True
        )

    # 👉 사람이 보기 좋은 이름으로 변경
    merged = merged.rename(columns={
        "승용_등록": "승용(등록)",
        "승용_폐차": "승용(폐차)",
        "승합_등록": "승합(등록)",
        "승합_폐차": "승합(폐차)",
        "화물_등록": "화물(등록)",
        "화물_폐차": "화물(폐차)",
        "특수_등록": "특수(등록)",
        "특수_폐차": "특수(폐차)",
        "총등록": "총등록",
        "총폐차": "총폐차",
    })

    # ---------------------------
    # 🎨 스타일링: 색 + 차종별 구분
    # ---------------------------
    blue = "#3366ff"  # 등록
    red = "#e60000"   # 폐차

    # 숫자 컬럼들
    num_cols = [c for c in merged.columns if c != "지역"]

    # 각 차종 그룹
    group_seungyong = ["승용(등록)", "승용(폐차)"]
    group_seunghap  = ["승합(등록)", "승합(폐차)"]
    group_hwamul    = ["화물(등록)", "화물(폐차)"]
    group_teuksu    = ["특수(등록)", "특수(폐차)"]
    group_total     = ["총등록", "총폐차"]

    # 등록/폐차 컬럼 분리
    scrap_cols = [c for c in merged.columns if "(폐차)" in c or c == "총폐차"]
    reg_cols   = [c for c in merged.columns if "(등록)" in c or c == "총등록"]

    styled = (
        merged.style
        # 천 단위 콤마
        .format("{:,}", subset=num_cols)
        # 폐차(파랑) / 등록(빨강)
        .set_properties(**{"color": blue}, subset=scrap_cols)
        .set_properties(**{"color": red}, subset=reg_cols)
        # 차종 그룹별 옅은 배경색 (살짝 구분)
        .set_properties(**{"background-color": "#fff5f5"}, subset=group_seungyong)
        .set_properties(**{"background-color": "#f5f7ff"}, subset=group_seunghap)
        .set_properties(**{"background-color": "#f5fff7"}, subset=group_hwamul)
        .set_properties(**{"background-color": "#f5ffff"}, subset=group_teuksu)
        .set_properties(**{"background-color": "#f0f0f0"}, subset=group_total)
        # 그룹 시작 컬럼에 세로 구분선 추가
        .set_properties(**{"border-left": "2px solid #cccccc"},
                        subset=["승용(등록)", "승합(등록)", "화물(등록)", "특수(등록)", "총등록"])
    )

    st.subheader("🚗 등록 · 폐차 통합 테이블")

    # 스타일링한 dataframe을 화면에 출력
    st.dataframe(styled, use_container_width=True)



    # 색상 정의
    red = "#e60000"
    blue = "#3366ff"

    st.subheader("🦋 등록 · 폐차 현황 비교 그래프(총합)")

    # ---------------------------
    # 6) 버터플라이 차트 (1) 전국 + 전체 → 지역별 등록 vs 폐차
    # ---------------------------
    if region == "전국" and year == "전체":
        merged = pd.merge(df_reg[["지역","총등록"]],
                        df_scrap[["지역","총폐차"]],
                        on="지역")
        merged["등록"] = -merged["총등록"]
        merged["폐차"] = merged["총폐차"]

        bf = pd.DataFrame({
            "지역": list(merged["지역"]) + list(merged["지역"]),
            "구분": ["등록"] * len(merged) + ["폐차"] * len(merged),
            "대수": list(merged["등록"]) + list(merged["폐차"])
        })

        # 🟡 툴팁에서 쓸 절대값 컬럼 따로 생성
        bf["표시대수"] = bf["대수"].abs()
        # y축에 표시할 지역 순서
        region_order = list(merged["지역"])

        chart = (
            alt.Chart(bf)
            .mark_bar() # altair로 수평 막대(bar)생성
            .encode(
                y=alt.Y("지역:N", sort=region_order),
                x=alt.X(
                    "대수:Q",
                    title="대수(등록=왼쪽 / 폐차=오른쪽)",
                    axis=alt.Axis(labelExpr="abs(datum.value)")
                ),
                color=alt.Color("구분:N", scale=alt.Scale(range=[red, blue])),
                tooltip=[
                    alt.Tooltip("지역:N", title="지역"),
                    alt.Tooltip("구분:N", title="구분"),
                    # ⬇ 여기서 실제 존재하는 컬럼 이름 사용
                    alt.Tooltip("표시대수:Q", title="대수")
                ]
            )
            .properties(height=450)
            .configure_axis(labelFontSize=16, titleFontSize=18)
            .configure_legend(labelFontSize=16, titleFontSize=18)
            .configure_title(fontSize=20)
        )
        st.altair_chart(chart, use_container_width=True)


    # ---------------------------
    # 7) 버터플라이 차트 (2) 나머지 케이스 → 차종별 등록 vs 폐차
    # ---------------------------
    else:
        if df_reg.empty or df_scrap.empty:
            st.warning("선택한 조건에 해당하는 비교 데이터가 없습니다.")
        else:
            # 이 경우 df_reg, df_scrap 은 1행(특정 지역 또는 전국 합계)이어야 함
            r = df_reg.iloc[0]
            s = df_scrap.iloc[0]

            df_compare = pd.DataFrame({
                "차종": ["승용","승합","화물","특수"],
                "등록": [-r["승용"], -r["승합"], -r["화물"], -r["특수"]],
                "폐차": [s["승용"], s["승합"], s["화물"], s["특수"]]
            })

            long_df = df_compare.melt(id_vars="차종", var_name="구분", value_name="대수")

            # 🟡 툴팁용 절대값 컬럼
            long_df["표시대수"] = long_df["대수"].abs()

            chart = (
                alt.Chart(long_df)
                .mark_bar()
                .encode(
                    y=alt.Y("차종:N", sort=["승용","승합","화물","특수"]),
                    x=alt.X(
                        "대수:Q",
                        title="대수(등록=왼쪽 / 폐차=오른쪽)",
                        axis=alt.Axis(labelExpr="abs(datum.value)")
                    ),
                    color=alt.Color("구분:N", scale=alt.Scale(range=[red, blue])),
                    tooltip=[
                        alt.Tooltip("차종:N", title="차종"),
                        alt.Tooltip("구분:N", title="구분"),
                        alt.Tooltip("표시대수:Q", title="대수")  # ⬅ 실제 있는 필드
                    ]
                )
                .properties(height=450)
                .configure_axis(labelFontSize=16, titleFontSize=18)
                .configure_legend(labelFontSize=16, titleFontSize=18)
                .configure_title(fontSize=20)
            )
            st.altair_chart(chart, use_container_width=True)


    # 커넥션 정리
    cursor.close()
    connection.close()

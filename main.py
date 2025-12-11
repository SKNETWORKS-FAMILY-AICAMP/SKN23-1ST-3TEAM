# main.py
import streamlit as st
from streamlit_option_menu import option_menu

# 페이지별 모듈 임포트
from tabs import registration, scrapping, comparison, faq

# ===============================
# 설정 및 CSS
# ===============================
st.set_page_config(page_title="자동차 현황", layout="wide")

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
/* 사이드바 너비 조정 */
section[data-testid="stSidebar"] {
    width: 330px !important;
}
</style>
            
            
""", unsafe_allow_html=True)

# ===============================
# Session State 초기값
# ===============================
if "selected_tab" not in st.session_state:

    # 석원 타이틀 수정(251210)
    st.session_state.selected_tab = "등록 현황"

# ===============================
# 사이드바 메뉴
# ===============================
with st.sidebar:
    # 석원 타이틀 수정(251210)
    st.markdown("""
        <div style='font-size:25px; font-weight:700; padding:12px 8px; color:#1d1d1f;'>
            자동차 데이터 통합 시스템 <br> 
        </div>
        <div style='font-size:20px; font-weight:700; margin-left:30px;  color:#1d1d1f;'>
            등록·폐차 현황 및 보험 FAQ  
        </div>
        <style>
        button[kind="header"] {
            position: fixed !important;
            left: 10px !important;
            top: 15px !important;
            z-index: 99999 !important;
        }
        [data-testid="collapsedControl"] {
            position: fixed !important;
            left: 10px !important;
            top: 15px !important;
            z-index: 99999 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    # 석원 타이틀 수정(251210)
    selected = option_menu(
        menu_title=None,
        options=["등록 현황", "폐차 현황", "등록 · 폐차 비교 현황", "자동차 보험 FAQ"],
        icons=["car-front", "trash", "columns-gap", "search"],
        default_index=["등록 현황", "폐차 현황", "등록 · 폐차 비교 현황", "자동차 보험 FAQ"].index(
            st.session_state.get("selected_tab", "등록 현황")
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

# ===============================
# 페이지 라우팅 (각 탭 실행)
# ===============================
# 석원 타이틀 수정(251210)
if selected == "등록 현황":
    registration.run()
elif selected == "폐차 현황":
    scrapping.run()
elif selected == "등록 · 폐차 비교 현황":
    comparison.run()
elif selected == "자동차 보험 FAQ":
    faq.run()
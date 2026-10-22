import html
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from bs4 import BeautifulSoup

# ==================================================
# 1. 페이지 설정
# ==================================================
st.set_page_config(
    page_title="CINEMA NOIR | 오늘의 박스오피스",
    page_icon="🎬",
    layout="wide",
)

KST = timezone(timedelta(hours=9))
TODAY_KST = datetime.now(KST).date()
YESTERDAY_KST = TODAY_KST - timedelta(days=1)

# ==================================================
# 2. 영화관 테마 CSS
# ==================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

.stApp {
    background:
        radial-gradient(ellipse at 15% 0%, #5a164333, transparent 38%),
        radial-gradient(ellipse at 90% 12%, #522a8433, transparent 34%),
        #100b16;
    color: #fff5fb;
    font-family: 'Noto Sans KR', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: #170f20;
}

h1, h2, h3, p, label {
    color: #fff5fb;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

.hero {
    padding: 28px 30px;
    border: 1px solid #ffffff20;
    border-radius: 24px;
    background: linear-gradient(
        120deg,
        #2c1027dd,
        #171020ee 65%,
        #21112fdd
    );
    box-shadow: 0 20px 60px #0005;
    margin-bottom: 24px;
}

.hero-kicker {
    color: #ff8da8;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 5px;
    margin-bottom: 10px;
}

.hero-title {
    font-size: clamp(30px, 4vw, 48px);
    line-height: 1.3;
    font-weight: 900;
    letter-spacing: -1.5px;
}

.hero-subtitle {
    color: #cbbad5;
    font-size: 14px;
    margin-top: 12px;
    line-height: 1.8;
}

.section-label {
    color: #ff8da8;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 3px;
    margin: 28px 0 12px;
}

.small-note {
    color: #b9a9c6;
    font-size: 12px;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #24162f, #17101f);
    border: 1px solid #ffffff18;
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 10px 28px #0003;
}

[data-testid="stMetricLabel"] {
    color: #c9b7d4 !important;
}

[data-testid="stMetricValue"] {
    color: #fff5fb !important;
    font-weight: 900;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background: #21162b;
    border-color: #ffffff2b;
    border-radius: 12px;
}

div[data-baseweb="select"] *,
div[data-baseweb="input"] * {
    color: #fff5fb;
}

/* 영화 티켓 */
.movie-ticket {
    --ticket-glow: #ff3155;
    display: grid;
    grid-template-columns: minmax(0, 1fr) 1px 230px;
    position: relative;
    overflow: hidden;
    border: 1px solid #ffffff30;
    border-radius: 22px;
    background:
        radial-gradient(
            ellipse at 0% 50%,
            #7f1d4b55,
            transparent 55%
        ),
        linear-gradient(
            135deg,
            #271323,
            #120d1c 70%,
            #20102c
        );
    box-shadow:
        0 20px 55px #0009,
        0 0 28px color-mix(
            in srgb

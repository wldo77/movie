# main.py
# CINEMA NOIR - 날짜별 박스오피스 대시보드
# KOBIS API + Google 이미지 검색
# 한국 시간 기준, 오늘은 선택할 수 없도록 설정

import datetime
import hashlib
import html
from urllib.parse import quote_plus, urlparse

import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from bs4 import BeautifulSoup


# ==================================================
# 1. 기본 설정과 한국 시간
# ==================================================

st.set_page_config(
    page_title="CINEMA NOIR | 박스오피스",
    page_icon="🎬",
    layout="wide",
)

KOBIS_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

GOOGLE_IMAGES_URL = "https://www.google.com/search"
KST = datetime.timezone(datetime.timedelta(hours=9))

# 배포 서버 시간대와 상관없이 한국 날짜를 계산합니다.
TODAY_KST = datetime.datetime.now(KST).date()
YESTERDAY = TODAY_KST - datetime.timedelta(days=1)


# ==================================================
# 2. 영화관 분위기 CSS
# ==================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

.stApp {
    background:
        radial-gradient(ellipse at 10% 5%, #40102d 0%, transparent 37%),
        radial-gradient(ellipse at 90% 25%, #251344 0%, transparent 40%),
        linear-gradient(150deg, #08070c, #120a17 55%, #08070c);
    color: #fff5fb;
    font-family: 'Noto Sans KR', sans-serif;
}

header[data-testid="stHeader"] { background: transparent; }

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

h1, h2, h3 { color: #fff5fb !important; }

.cinema-kicker {
    color: #ff718e;
    letter-spacing: 5px;
    font-size: 11px;
    font-weight: 900;
}

.cinema-title {
    font-family: 'Black Han Sans', 'Noto Sans KR', sans-serif;
    font-size: clamp(36px, 5vw, 64px);
    line-height: 1.2;
    letter-spacing: -2px;
    color: #fff7fc;
    text-shadow: 0 0 30px #ff315544;
    margin: 10px 0;
}

.cinema-subtitle {
    color: #b7a7c2;
    font-size: 14px;
    line-height: 1.9;
}

.section-label {
    color: #ff829a;
    letter-spacing: 3px;
    font-size: 11px;
    font-weight: 900;
    margin-bottom: 10px;
}

.rank-chip {
    display: inline-block;
    border: 1px solid #ff4c6e88;
    background: #ff31551c;
    color: #ff8da4;
    border-radius: 100px;
    padding: 7px 13px;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 2

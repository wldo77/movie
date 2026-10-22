# main.py
# CINEMA NOIR - 날짜별 박스오피스 대시보드
# KOBIS API를 이용하고, Google 이미지 검색으로 포스터를 찾아봅니다.

import datetime
import hashlib
import html
from urllib.parse import urlparse

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from bs4 import BeautifulSoup


# 1. 페이지 설정 및 한국 날짜 계산
st.set_page_config(page_title="CINEMA NOIR | 박스오피스", page_icon="🎬", layout="wide")

KOBIS_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)
GOOGLE_IMAGES_URL = "https://www.google.com/search"
KST = datetime.timezone(datetime.timedelta(hours=9))
TODAY_KST = datetime.datetime.now(KST).date()
YESTERDAY = TODAY_KST - datetime.timedelta(days=1)


# 2. 영화관 테마 디자인
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
.stApp{background:radial-gradient(ellipse at 10% 5%,#40102d 0%,transparent 37%),radial-gradient(ellipse at 90% 25%,#251344 0%,transparent 40%),linear-gradient(150deg,#08070c,#120a17 55%,#08070c);color:#fff5fb;font-family:'Noto Sans KR',sans-serif}
header[data-testid="stHeader"]{background:transparent}.block-container{max-width:1250px;padding-top:2rem;padding-bottom:4rem}h1,h2,h3{color:#fff5fb!important}
.cinema-kicker{color:#ff718e;letter-spacing:5px;font-size:11px;font-weight:900}.cinema-title{font-family:'Black Han Sans','Noto Sans KR',sans-serif;font-size:clamp(36px,5vw,64px);line-height:1.2;letter-spacing:-2px;color:#fff7fc;text-shadow:0 0 30px #ff315544;margin:10px 0}.cinema-subtitle{color:#b7a7c2;font-size:14px;line-height:1.9}
.section-label{color:#ff829a;letter-spacing:3px;font-size:11px;font-weight:900;margin-bottom:10px}.rank-chip{display:inline-block;border:1px solid #ff4c6e88;background:#ff31551c;color:#ff8da4;border-radius:100px;padding:7px 13px;font-size:11px;font-weight:900;letter-spacing:2px}
.movie-stage{position:relative;overflow:hidden;border:1px solid #ffffff20;border-radius:25px;padding:30px;background:radial-gradient(ellipse at 5% 50%,var(--glow,#ff315544),transparent 52%),linear-gradient(125deg,#21101f,#100d18 55%,#1c0c24);box-shadow:0 24px 75px #0009,inset 0 1px #ffffff0d}.movie-stage-content{position:relative;z-index:1}.movie-name{color:#fff;font-size:clamp(25px,3.5vw,43px);line-height:1.35;font-weight:900;letter-spacing:-1px;margin:18px 0 12px;overflow-wrap:anywhere;text-shadow:0 4px 25px #0008}.movie-meta{color:#c6b6ce;font-size:13px;line-height:2}.movie-description{margin-top:20px;padding:13px 15px;border-left:2px solid var(--glow,#ff3155);background:#ffffff08;color:#e5d8e9;font-size:13px;line-height:1.9}
.poster-wrap{perspective:1100px;padding:8px 12px 18px}.poster-card{position:relative;max-width:285px;margin:auto;transform:rotateY(-10deg) rotateX(2deg);transform-style:preserve-3d;border-radius:13px;transition:transform .5s ease,filter .5s ease;box-shadow:17px 22px 30px #000a,0 0 24px var(--glow,#ff315566),0 0 70px var(--glow,#a855f733)}.poster-card:hover{transform:rotateY(0deg) rotateX(0deg) translateY(-7px) scale(1.025);filter:brightness(1.08)}.poster-card img{display:block;width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:12px;border:1px solid #ffffff38}
.poster-placeholder{aspect-ratio:2/3;border-radius:12px;border:1px solid #ffffff33;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:18px;background:radial-gradient(ellipse at 50% 35%,var(--glow,#a855f7),transparent 65%),linear-gradient(155deg,#30132e,#100b19 65%,#08070d);color:white;overflow-wrap:anywhere}.poster-number{font-size:11px;letter-spacing:5px;color:#ffd6e3}.poster-film-title{font-family:'Black Han Sans',sans-serif;font-size:29px;line-height:1.4;margin:22px 0;text-shadow:0 3px 18px #000b}.poster-caption{color:#f2c9dc;font-size:10px;letter-spacing:3px}.poster-foot{text-align:center;color:#c8afce;font-size:10px;letter-spacing:3px;margin-top:13px}
.metric-card{padding:21px;min-height:118px;background:linear-gradient(140deg,#211320,#120e19);border:1px solid #ffffff18;border-radius:17px;box-shadow:0 10px 30px #0005}.metric-label{color:#bca8c7;font-size:12px;margin-bottom:12px}.metric-value{color:#fff4fb;font-size:clamp(22px,2.5vw,30px);font-weight:900;letter-spacing:-1px;overflow-wrap:anywhere}.metric-note{color:#ff7897;font-size:11px;margin-top:8px}.cinema-divider{height:1px;background:linear-gradient(90deg,transparent,#ff315588,#a855f788,transparent);margin:28px 0}
div[data-testid="stDataFrame"]{border:1px solid #ffffff1c;border-radius:12px;overflow:hidden}@media(max-width:700px){.movie-stage{padding:19px}.poster-wrap{padding:5px 0 20px}.poster-card{max-width:210px}}
</style>
    """,
    unsafe_allow_html=True,
)


# 3. 공통 도우미 함수
def safe_int(value):
    """문자열 숫자를 안전하게 정수로 변환합니다."""
    try:
        return int(float(str(value).replace(",", "")))
    except (ValueError, TypeError):
        return 0


def safe_text(value, fallback="정보 없음"):
    """빈 값이나 None을 기본 문구로 바꿉니다."""
    if value is None or not str(value).strip():
        return fallback
    return str(value).strip()


def movie_color(movie_name):
    """영화명마다 붉은색·보라색 조명을 하나씩 지정합니다."""
    digest = hashlib.md5(movie_name.encode("utf-8")).hexdigest()
    palette = [
        "#ff3155", "#b04cff", "#ff6b35", "#8b5cf6",
        "#e83e8c", "#d946ef", "#fb7185", "#7c3aed",
    ]
    return palette[int(digest[:4], 16) % len(palette)]


# 4. KOBIS 일별 박스오피스 API
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_boxoffice(target_date, api_key):
    response = requests.get(
        KOBIS_URL,
        params={"key": api_key, "targetDt": target_date},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


# 5. Google 이미지 검색으로 포스터 찾기
@st.cache_data(ttl=86400, show_spinner=False)
def google_poster_search(movie_name, open_date):
    """Google 이미지 검색 페이지에서 썸네일 주소를 시도합니다."""
    query = f"{movie_name} 영화 포스터"
    if open_date and len(open_date) >= 4 and open_date[:4].isdigit():
        query += f" {open_date[:4]}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    }

    try:
        response = requests.get(
            GOOGLE_IMAGES_URL,
            params={"tbm": "isch", "q": query, "hl": "ko", "gl": "kr"},
            headers=headers,
            timeout=12,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            if not src.startswith(("https://", "http://")):
                continue
            host = urlparse(src).hostname or ""
            if host.startswith("encrypted-tbn") and host.endswith(".gstatic.com"):
                return src
        return None
    except (requests.RequestException, ValueError):
        return None


# 6. 포스터 또는 대체 포스터 표시
def render_poster(movie_name, poster_url, glow):
    escaped_name = html.escape(movie_name)

    if poster_url:
        poster_content = f"""
        <img src="{html.escape(poster_url, quote=True)}"
             alt="{escaped_name} 포스터"
             onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
        <div class="poster-placeholder" style="display:none; --glow:{glow};">
            <div class="poster-number">CINEMA NOIR</div>
            <div class="poster-film-title">{escaped_name}</div>
            <div class="poster-caption">NOW SHOWING</div>
        </div>
        """
    else:
        poster_content = f"""
        <div class="poster-placeholder" style="--glow:{glow};">
            <div class="poster-number">CINEMA NOIR</div>
            <div class="poster-film-title">{escaped_name}</div>
            <div class="poster-caption">NOW SHOWING</div>
        </div>
        """

    st.markdown(
        f"""
        <div class="poster-wrap">
            <div class="poster-card" style="--glow:{glow};">
                {poster_content}
            </div>
            <div class="poster-foot">★ FEATURED FILM ★</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# 7. 앱 제목과 소개
st.markdown(
    """
    <div class="cinema-kicker">THE DAILY BOX OFFICE EXPERIENCE</div>
    <div class="cinema-title">CINEMA NOIR</div>
    <div class="cinema-subtitle">
        영화관의 붉은 조명 아래, 흥행의 기록을 확인하다.<br>
        RED LIGHTS · PURPLE SHADOWS · MOVIE NIGHT
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div class="cinema-divider"></div>', unsafe_allow_html=True)


# 8. 날짜 선택: 한국 시간 기준 오늘은 선택할 수 없습니다.
st.markdown(
    '<div class="section-label">01 / SELECT SCREENING DATE</div>',
    unsafe_allow_html=True,
)
selected_date = st.date_input(
    "보고 싶은 날짜를 선택하세요",
    value=YESTERDAY,
    min_value=datetime.date(2004, 1, 1),
    max_value=YESTERDAY,
    format="YYYY/MM/DD",
    help="집계 중인 오늘은 선택할 수 없습니다.",
)
TARGET_DT = selected_date.strftime("%Y%m%d")
st.caption(
    f"선택한 조회 날짜: {selected_date.strftime('%Y년 %m월 %d일')} "
    "| 오늘 이전 날짜만 선택할 수 있습니다."
)


# 9. 비밀 금고에서 KOBIS 인증키 읽기
try:
    KOBIS_KEY = str(st.secrets["KOBIS_KEY"]).strip()
except (KeyError, FileNotFoundError):
    st.error("KOBIS_KEY 인증키를 찾을 수 없습니다.")
    st.info(
        "Streamlit Cloud → 앱 설정 → Secrets에서 다음 형식으로 등록해 주세요: "
        'KOBIS_KEY = "발급받은_인증키"'
    )
    st.stop()

if not KOBIS_KEY:
    st.error("KOBIS_KEY가 비어 있습니다. Secrets 설정을 확인해 주세요.")
    st.stop()


# 10. API 호출 및 오류 안내
try:
    with st.spinner("🎞️ 선택한 날짜의 박스오피스를 불러오는 중..."):
        data = fetch_boxoffice(TARGET_DT, KOBIS_KEY)
except requests.exceptions.Timeout:
    st.error("KOBIS 서버의 응답 시간이 초과되었습니다.")
    st.info("잠시 후 새로고침해 주세요.")
    st.stop()
except requests.exceptions.HTTPError as error:
    st.error("KOBIS 서버에서 HTTP 오류가 발생했습니다.")
    st.info(f"HTTP 오류: {error}")
    st.stop()
except requests.exceptions.RequestException as error:
    st.error("KOBIS 서버에 연결하지 못했습니다.")
    st.info(f"인터넷 연결과 API 주소를 확인해 주세요. ({error})")
    st.stop()
except ValueError:
    st.error("KOBIS 응답을 JSON으로 읽을 수 없습니다.")
    st.info("KOBIS 서버의 응답 상태를 확인해 주세요.")
    st.stop()

if not isinstance(data, dict):
    st.error("KOBIS 응답 형식이 올바르지 않습니다.")
    st.stop()

# 인증키 오류도 HTTP 200으로 올 수 있으므로 faultInfo를 확인합니다.
if "faultInfo" in data:
    fault = data.get("faultInfo", {})
    if isinstance(fault, dict):
        error_code = fault.get("errorCode", "확인되지 않음")
        error_message = fault.get("message", "오류 메시지가 없습니다.")
    else:
        error_code = "확인되지 않음"
        error_message = str(fault)
    st.error("KOBIS API에서 오류를 반환했습니다.")
    st.write(f"오류 코드: {error_code}")
    st.write(f"오류 내용: {error_message}")
    st.info("KOBIS_KEY가 올바르게 등록되었는지 확인해 주세요.")
    st.stop()

boxoffice_result = data.get("boxOfficeResult")
if not isinstance(boxoffice_result, dict):
    st.error("박스오피스 결과를 찾을 수 없습니다.")
    st.info("KOBIS API 응답 구조를 확인해 주세요.")
    st.stop()

movies = boxoffice_result.get("dailyBoxOfficeList", [])
if not isinstance(movies, list) or len(movies) == 0:
    st.warning("그날은 아직 집계 전입니다")
    st.info(
        "해당 날짜의 영화 목록이 비어 있습니다. KOBIS 집계가 아직 끝나지 "
        "않았거나 자료가 제공되지 않았을 수 있습니다. 다른 날짜를 선택하거나 "
        "잠시 후 다시 확인해 주세요."
    )
    st.stop()


# 11. 표와 그래프에 사용할 데이터 정리
df = pd.DataFrame(movies)
for col in ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]:
    if col not in df.columns:
        df[col] = 0
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

for col in ["movieNm", "openDt"]:
    if col not in df.columns:
        df[col] = ""
    df[col] = df[col].fillna("").astype(str)

df = df[df["movieNm"].str.strip() != ""]
df = df.sort_values("rank").reset_index(drop=True)
if df.empty:
    st.warning("그날은 아직 집계 전입니다")
    st.info("KOBIS 응답에 표시할 영화명이 없습니다.")
    st.stop()


# 12. 순위 변동 및 트로피 표시
def rank_change_label(value):
    """rankInten 양수는 상승, 음수는 하락으로 표시합니다."""
    change = safe_int(value)
    if change > 0:
        return f"↑ +{change}"
    if change < 0:
        return f"↓ {change}"
    return "— 0"


def rank_change_style(value):
    """순위 상승은 빨간색, 하락은 파란색으로 표시합니다."""
    value = str(value)
    if value.startswith("↑"):
        return "color: #ff365d; font-weight: bold;"
    if value.startswith("↓"):
        return "color: #55aaff; font-weight: bold;"
    return "color: #aaa0b4;"


def displayed_movie_name(row):
    """누적 관객수가 100만 명을 넘으면 영화명 옆에 트로피를 붙입니다."""
    name = safe_text(row["movieNm"], "영화명 없음")
    return f"🏆 {name}" if safe_int(row["audiAcc"]) > 1_000_000 else name


df["displayName"] = df.apply(displayed_movie_name, axis=1)
df["rankChange"] = df["rankInten"].apply(rank_change_label)


# 13. 1위 영화와 포스터
winner = df.iloc[0]
winner_name = safe_text(winner["movieNm"], "영화명 없음")
winner_title = displayed_movie_name(winner)
winner_open = safe_text(winner["openDt"], "개봉일 정보 없음")
winner_color = movie_color(winner_name)

with st.spinner("🖼️ Google에서 영화 포스터를 찾는 중..."):
    poster_url = google_poster_search(winner_name, winner_open)

st.markdown(
    '<div class="section-label">02 / THE FEATURED FILM</div>',
    unsafe_allow_html=True,
)
left, right = st.columns([1.35, 0.85], gap="large")

with left:
    st.markdown(
        f"""
        <div class="movie-stage" style="--glow:{winner_color}55;">
            <div class="movie-stage-content">
                <span class="rank-chip">🏆 BOX OFFICE NO. 1</span>
                <div class="movie-name">{html.escape(winner_title)}</div>
                <div class="movie-meta">
                    조회 날짜 &nbsp; {selected_date.strftime('%Y.%m.%d')}<br>
                    개봉일 &nbsp; {html.escape(winner_open)}
                </div>
                <div class="movie-description">
                    선택한 날짜의 박스오피스 1위 영화입니다.<br>
                    오늘의 스포트라이트를 차지한 흥행의 주인공!
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    render_poster(winner_name, poster_url, winner_color)
    # Google에서 직접 검색할 수 있는 링크도 함께 제공합니다.
    google_query = requests.utils.quote(f"{winner_name} 영화 포스터")
    google_link = f"https://www.google.com/search?tbm=isch&q={google_query}"
    st.link_button(
        "🔎 Google에서 포스터 검색",
        google_link,
        use_container_width=True,
    )
    if poster_url:
        st.caption(
            "Google 이미지 검색 결과의 썸네일입니다. "
            "동명 영화면 포스터가 다를 수 있습니다."
        )
    else:
        st.caption(
            "자동으로 포스터를 불러오지 못했습니다. "
            "위 링크에서 직접 확인할 수 있습니다."
        )


# 14. 1위 영화 지표 카드 세 장
st.markdown('<div class="cinema-divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-label">03 / THE BOX OFFICE NUMBERS</div>',
    unsafe_allow_html=True,
)
m1, m2, m3 = st.columns(3)

metrics = [
    (m1, "🎟️ 관객수", safe_int(winner["audiCnt"]), "SELECTED DAY"),
    (m2, "👥 누적관객", safe_int(winner["audiAcc"]), "TOTAL AUDIENCE"),
    (m3, "🎬 스크린수", safe_int(winner["scrnCnt"]), "SCREENS"),
]

for col, label, value, note in metrics:
    with col:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value:,}</div>
                <div class="metric-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# 15. 전체 박스오피스 표
st.markdown('<div class="cinema-divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-label">04 / THE FULL CAST</div><h2>🎞️ 전체 박스오피스</h2>',
    unsafe_allow_html=True,
)

table = df[
    [
        "rank", "displayName", "openDt", "rankChange",
        "audiCnt", "audiAcc", "scrnCnt"
    ]
].copy()

table.columns = [
    "순위", "영화명", "개봉일", "순위 변동",
    "관객수", "누적관객", "스크린수"
]

for col in ["순위", "관객수", "누적관객", "스크린수"]:
    table[col] = table[col].map(lambda value: f"{int(value):,}")

styled_table = table.style.map(
    rank_change_style,
    subset=["순위 변동"],
)

st.dataframe(
    styled_table,
    hide_index=True,
    use_container_width=True,
    height=min(600, 40 * (len(table) + 1)),
)


# 16. 관객수 상위 5편 막대그래프
st.markdown('<div class="cinema-divider"></div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="section-label">05 / AUDIENCE CHART</div>
    <h2>📊 관객수 TOP 5</h2>
    <p style="color:#b7a7c2;font-size:13px;">
        선택한 날짜의 관객수가 많은 영화 다섯 편
    </p>
    """,
    unsafe_allow_html=True,
)

top5 = df.sort_values("audiCnt", ascending=False).head(5).copy()
top5["조명색"] = top5["movieNm"].apply(movie_color)

fig = px.bar(
    top5.sort_values("audiCnt", ascending=True),
    x="audiCnt",
    y="displayName",
    orientation="h",
    text="audiCnt",
    color="조명색",
    color_discrete_map="identity",
    labels={"audiCnt": "관객수(명)", "displayName": "영화명"},
)

fig.update_traces(
    texttemplate="%{text:,.0f}명",
    textposition="outside",
    cliponaxis=False,
)

fig.update_layout(
    height=360,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f7eefa", family="Noto Sans KR"),
    xaxis=dict(
        title="관객수(명)",
        tickformat=",",
        gridcolor="#ffffff12",
        zerolinecolor="#ffffff22",
    ),
    yaxis=dict(title="", gridcolor="rgba(0,0,0,0)"),
    margin=dict(l=10, r=90, t=20, b=15),
    showlegend=False,
)

st.plotly_chart(fig, use_container_width=True)


# 17. 하단 안내
st.markdown('<div class="cinema-divider"></div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <div style="text-align:center;padding:15px 0 5px;">
        <div style="color:#ff6b89;font-size:11px;letter-spacing:4px;">
            END OF SCREENING
        </div>
        <div style="color:#a99ab4;font-size:12px;margin-top:10px;line-height:2;">
            DATA SOURCE · KOBIS 영화관입장권통합전산망<br>
            POSTER SEARCH · Google 이미지 검색<br>
            SELECTED DATE · {selected_date.strftime('%Y-%m-%d')}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

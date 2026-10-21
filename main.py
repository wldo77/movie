```python
# main.py
# 어제의 박스오피스 - CINEMA NOIR
# KOBIS 공식 API + 선택적 TMDB 영화 포스터 검색

import datetime
import hashlib
import html
import requests
import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="CINEMA NOIR | 박스오피스",
    page_icon="🎬",
    layout="wide",
)

KOBIS_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w780"

# 서버의 시간대가 아니라 한국 시간(UTC+9)을 기준으로 날짜 계산
KST = datetime.timezone(datetime.timedelta(hours=9))
TODAY_KST = datetime.datetime.now(KST).date()
YESTERDAY = TODAY_KST - datetime.timedelta(days=1)
TARGET_DT = YESTERDAY.strftime("%Y%m%d")


# --------------------------------------------------
# 2. 영화관 스타일 CSS
# --------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

:root {
    --bg: #09070d;
    --panel: #15101c;
    --red: #ff3155;
    --purple: #a855f7;
    --muted: #a69aaf;
}

.stApp {
    background:
        radial-gradient(ellipse at 12% 5%, #3b102b 0%, transparent 35%),
        radial-gradient(ellipse at 90% 28%, #21123f 0%, transparent 38%),
        linear-gradient(160deg, #09070d 0%, #100a14 55%, #08070c 100%);
    color: #fff5fb;
    font-family: 'Noto Sans KR', sans-serif;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

h1, h2, h3 {
    color: #fff5fb !important;
    font-family: 'Noto Sans KR', sans-serif;
}

.cinema-kicker {
    color: #ff6b89;
    letter-spacing: 5px;
    font-size: 11px;
    font-weight: 900;
    text-transform: uppercase;
}

.cinema-title {
    font-family: 'Black Han Sans', 'Noto Sans KR', sans-serif;
    font-size: clamp(36px, 5vw, 64px);
    line-height: 1.15;
    letter-spacing: -2px;
    margin: 10px 0;
    color: #fff7fc;
    text-shadow: 0 0 30px #ff315533;
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
    margin-bottom: 8px;
}

.movie-stage {
    position: relative;
    overflow: hidden;
    border: 1px solid #ffffff18;
    border-radius: 25px;
    padding: 30px;
    background:
        radial-gradient(ellipse at 5% 50%, var(--glow, #ff315533), transparent 48%),
        linear-gradient(125deg, #1d101f 0%, #100d18 48%, #1a0c20 100%);
    box-shadow: 0 24px 75px #0009, inset 0 1px #ffffff0d;
}

.movie-stage:before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background: repeating-linear-gradient(
        115deg,
        transparent 0px,
        transparent 60px,
        #ffffff04 61px,
        transparent 63px
    );
}

.movie-stage-content {
    position: relative;
    z-index: 1;
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
    letter-spacing: 2px;
}

.movie-name {
    color: white;
    font-size: clamp(25px, 3.4vw, 43px);
    line-height: 1.3;
    font-weight: 900;
    letter-spacing: -1px;
    margin: 18px 0 12px;
    overflow-wrap: anywhere;
    text-shadow: 0 4px 25px #0008;
}

.movie-meta {
    color: #c6b6ce;
    font-size: 13px;
    line-height: 2;
}

.movie-description {
    margin-top: 20px;
    padding: 13px 15px;
    border-left: 2px solid var(--glow, #ff3155);
    background: #ffffff07;
    color: #e5d8e9;
    font-size: 13px;
    line-height: 1.9;
}

.poster-wrap {
    perspective: 1100px;
    padding: 8px 12px 18px;
}

.poster-card {
    position: relative;
    max-width: 285px;
    margin: auto;
    transform: rotateY(-10deg) rotateX(2deg);
    transform-style: preserve-3d;
    border-radius: 13px;
    transition: transform .5s ease, filter .5s ease;
    box-shadow:
        17px 22px 30px #000a,
        0 0 24px var(--glow, #ff315566),
        0 0 70px var(--glow, #a855f733);
}

.poster-card:hover {
    transform: rotateY(0deg) rotateX(0deg) translateY(-7px) scale(1.025);
    filter: brightness(1.08);
}

.poster-card img {
    display: block;
    width: 100%;
    aspect-ratio: 2 / 3;
    object-fit: cover;
    border-radius: 12px;
    border: 1px solid #ffffff38;
}

.poster-placeholder {
    aspect-ratio: 2 / 3;
    border-radius: 12px;
    border: 1px solid #ffffff33;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 18px;
    background:
        radial-gradient(ellipse at 50% 35%, var(--glow, #a855f7) 0%, transparent 65%),
        linear-gradient(155deg, #30132e, #100b19 65%, #08070d);
    color: white;
    overflow-wrap: anywhere;
}

.poster-placeholder .poster-number {
    font-size: 11px;
    letter-spacing: 5px;
    color: #ffd6e3;
}

.poster-placeholder .poster-film-title {
    font-family: 'Black Han Sans', sans-serif;
    font-size: 29px;
    line-height: 1.4;
    margin: 22px 0;
    text-shadow: 0 3px 18px #000b;
}

.poster-placeholder .poster-caption {
    color: #f2c9dc;
    font-size: 10px;
    letter-spacing: 3px;
}

.poster-foot {
    text-align: center;
    color: #c8afce;
    font-size: 10px;
    letter-spacing: 3px;
    margin-top: 13px;
}

.metric-card {
    padding: 21px;
    min-height: 118px;
    background: linear-gradient(140deg, #211320, #120e19);
    border: 1px solid #ffffff15;
    border-radius: 17px;
    box-shadow: 0 10px 30px #0005;
}

.metric-label {
    color: #bca8c7;
    font-size: 12px;
    margin-bottom: 12px;
}

.metric-value {
    color: #fff4fb;
    font-size: clamp(22px, 2.5vw, 30px);
    font-weight: 900;
    letter-spacing: -1px;
    overflow-wrap: anywhere;
}

.metric-note {
    color: #ff7897;
    font-size: 11px;
    margin-top: 8px;
}

.cinema-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #ff315588, #a855f788, transparent);
    margin: 28px 0;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #ffffff1c;
    border-radius: 12px;
    overflow: hidden;
}

div[data-testid="stAlert"] {
    border-radius: 12px;
}

.stCaption {
    color: #a99ab4;
}

footer {
    visibility: hidden;
}

@media (max-width: 700px) {
    .movie-stage {
        padding: 19px;
    }
    .poster-wrap {
        padding: 5px 0 20px;
    }
    .poster-card {
        max-width: 210px;
    }
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# 3. 공통 도우미 함수
# --------------------------------------------------

def safe_int(value):
    """API의 문자열 숫자를 안전하게 정수로 변환합니다."""
    try:
        return int(float(str(value).replace(",", "")))
    except (ValueError, TypeError):
        return 0


def safe_text(value, fallback="정보 없음"):
    """비어 있는 문자열이나 None을 화면에 맞게 처리합니다."""
    if value is None or not str(value).strip():
        return fallback
    return str(value).strip()


def movie_color(movie_name):
    """영화명에 따라 붉은색 또는 보라색 계열의 조명을 정합니다."""
    digest = hashlib.md5(movie_name.encode("utf-8")).hexdigest()
    palette = [
        "#ff3155",
        "#b04cff",
        "#ff6b35",
        "#8b5cf6",
        "#e83e8c",
        "#d946ef",
        "#fb7185",
        "#7c3aed",
    ]
    return palette[int(digest[:4], 16) % len(palette)]


# --------------------------------------------------
# 4. KOBIS 박스오피스 데이터
# --------------------------------------------------

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_boxoffice(target_date, api_key):
    """KOBIS에서 일별 박스오피스를 조회합니다."""
    response = requests.get(
        KOBIS_URL,
        params={
            "key": api_key,
            "targetDt": target_date,
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


# --------------------------------------------------
# 5. 선택적 TMDB 포스터 검색
# --------------------------------------------------

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_poster(movie_name, open_date, tmdb_key):
    """
    TMDB에서 영화 포스터를 검색합니다.
    TMDB_KEY가 없거나 검색 결과가 없으면 None을 반환합니다.
    """
    if not tmdb_key:
        return None

    params = {
        "api_key": tmdb_key,
        "query": movie_name,
        "language": "ko-KR",
        "include_adult": "false",
    }

    # 개봉 연도가 있으면 검색 정확도를 높입니다.
    if open_date and len(open_date) >= 4 and open_date[:4].isdigit():
        params["year"] = open_date[:4]

    try:
        response = requests.get(
            TMDB_SEARCH_URL,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        results = response.json().get("results", [])

        if not results:
            return None

        # 포스터가 있는 검색 결과를 우선 선택합니다.
        results = sorted(
            results,
            key=lambda item: bool(item.get("poster_path")),
            reverse=True,
        )

        for result in results:
            poster_path = result.get("poster_path")
            if poster_path:
                return TMDB_IMAGE_URL + poster_path

        return None

    except (requests.RequestException, ValueError, TypeError):
        # 포스터 검색에 실패해도 박스오피스 화면은 계속 표시합니다.
        return None


# --------------------------------------------------
# 6. 포스터 HTML 만들기
# --------------------------------------------------

def render_poster(movie_name, poster_url, glow):
    """실제 포스터 또는 대체 포스터를 입체적인 카드로 표시합니다."""
    escaped_name = html.escape(movie_name)

    if poster_url:
        # 이미지 주소는 TMDB API가 반환한 주소를 사용합니다.
        poster_content = f"""
        <img src="{html.escape(poster_url, quote=True)}"
             alt="{escaped_name} 포스터"
             onerror="this.style.display='none';
             this.nextElementSibling.style.display='flex';">
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


# --------------------------------------------------
# 7. 영화관 스타일 제목
# --------------------------------------------------

st.markdown(
    """
    <div class="cinema-kicker">THE DAILY BOX OFFICE EXPERIENCE</div>
    <div class="cinema-title">CINEMA NOIR</div>
    <div class="cinema-subtitle">
        어제의 흥행 기록을 스크린 위에 펼치다.<br>
        RED LIGHTS · PURPLE SHADOWS · MOVIE NIGHT
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div style="margin-top:22px; margin-bottom:12px;">
        <span class="rank-chip">DAILY BOX OFFICE</span>
        <span style="color:#b7a7c2; font-size:12px; margin-left:10px;">
            조회 기준 · {YESTERDAY.strftime('%Y년 %m월 %d일')}
            (한국 시간)
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# 8. 인증키 읽기
# --------------------------------------------------

try:
    KOBIS_KEY = str(st.secrets["KOBIS_KEY"]).strip()
except (KeyError, FileNotFoundError):
    st.error("KOBIS_KEY 인증키가 등록되지 않았습니다.")
    st.info(
        "Streamlit Cloud → 앱 설정 → Secrets에서 "
        'KOBIS_KEY = "발급받은_인증키" 를 등록해 주세요.'
    )
    st.stop()

if not KOBIS_KEY:
    st.error("KOBIS_KEY가 비어 있습니다. Secrets 설정을 확인해 주세요.")
    st.stop()

# TMDB 키는 선택 사항입니다.
# 등록하지 않아도 순위표와 대체 포스터는 정상적으로 표시됩니다.
try:
    TMDB_KEY = str(st.secrets.get("TMDB_KEY", "")).strip()
except Exception:
    TMDB_KEY = ""


# --------------------------------------------------
# 9. KOBIS API 호출 및 오류 안내
# --------------------------------------------------

try:
    with st.spinner("🎞️ 상영관의 불을 켜는 중입니다..."):
        data = fetch_boxoffice(TARGET_DT, KOBIS_KEY)

except requests.exceptions.Timeout:
    st.error("KOBIS 서버 응답 시간이 초과되었습니다.")
    st.info("잠시 후 앱을 새로고침해 주세요.")
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

if "faultInfo" in data:
    fault = data.get("faultInfo", {})
    if isinstance(fault, dict):
        code = fault.get("errorCode", "확인되지 않음")
        message = fault.get("message", "오류 메시지가 없습니다.")
    else:
        code = "확인되지 않음"
        message = str(fault)

    st.error("KOBIS API에서 오류를 반환했습니다.")
    st.write(f"오류 코드: {code}")
    st.write(f"오류 내용: {message}")
    st.info("KOBIS_KEY가 올바른지, 발급 상태가 정상인지 확인해 주세요.")
    st.stop()

boxoffice_result = data.get("boxOfficeResult")

if not isinstance(boxoffice_result, dict):
    st.error("박스오피스 결과를 찾을 수 없습니다.")
    st.info("KOBIS API 응답 구조를 확인해 주세요.")
    st.stop()

movies = boxoffice_result.get("dailyBoxOfficeList", [])

if not isinstance(movies, list) or not movies:
    st.warning("해당 날짜의 영화 목록이 비어 있습니다.")
    st.info(
        "KOBIS 집계가 완료되지 않았거나 자료가 없는 날짜일 수 있습니다. "
        "조회 날짜와 API 응답을 확인해 주세요."
    )
    st.stop()


# --------------------------------------------------
# 10. 데이터 정리
# --------------------------------------------------

df = pd.DataFrame(movies)

for col in ["rank", "audiCnt", "audiAcc", "scrnCnt"]:
    if col not in df.columns:
        df[col] = 0
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

for col in ["movieNm", "openDt", "movieCd"]:
    if col not in df.columns:
        df[col] = ""

df["movieNm"] = df["movieNm"].fillna("").astype(str)
df["openDt"] = df["openDt"].fillna("").astype(str)
df["movieCd"] = df["movieCd"].fillna("").astype(str)

df = df[df["movieNm"].str.strip() != ""]
df = df.sort_values("rank").reset_index(drop=True)

if df.empty:
    st.warning("표시할 영화 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# 11. 1위 영화 무대
# --------------------------------------------------

winner = df.iloc[0]
winner_name = safe_text(winner["movieNm"], "영화명 없음")
winner_open = safe_text(winner["openDt"], "개봉일 정보 없음")
winner_color = movie_color(winner_name)

# 포스터는 캐시되어 반복 조회 시 빠르게 표시됩니다.
poster_url = fetch_poster(winner_name, winner_open, TMDB_KEY)

st.markdown(
    f"""
    <div class="cinema-divider"></div>
    <div class="section-label">01 / TONIGHT'S HEADLINER</div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.35, 0.85], gap="large")

with left:
    st.markdown(
        f"""
        <div class="movie-stage" style="--glow:{winner_color}55;">
            <div class="movie-stage-content">
                <span class="rank-chip">🏆 BOX OFFICE NO. 1</span>
                <div class="movie-name">{html.escape(winner_name)}</div>
                <div class="movie-meta">
                    RELEASE DATE &nbsp; {html.escape(winner_open)}<br>
                    DAILY RANK &nbsp; 01
                </div>
                <div class="movie-description">
                    오늘의 스포트라이트를 차지한 영화.<br>
                    어제의 관객들이 선택한 흥행의 주인공입니다.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    render_poster(winner_name, poster_url, winner_color)

if not TMDB_KEY:
    st.caption(
        "실제 영화 포스터를 표시하려면 TMDB_KEY를 Secrets에 추가하세요. "
        "현재는 영화명 기반의 시네마 포스터를 표시합니다."
    )
elif not poster_url:
    st.caption(
        "이 영화의 포스터를 찾지 못했습니다. "
        "영화명이나 TMDB 검색 결과를 확인해 주세요."
    )


# --------------------------------------------------
# 12. 1위 영화 지표 카드 세 장
# --------------------------------------------------

st.markdown(
    '<div class="section-label">02 / THE NUMBERS BEHIND THE MAGIC</div>',
    unsafe_allow_html=True,
)

m1, m2, m3 = st.columns(3)

metrics = [
    (m1, "🎟️ 어제 관객수", safe_int(winner["audiCnt"]), "DAILY AUDIENCE"),
    (m2, "👥 누적 관객수", safe_int(winner["audiAcc"]), "TOTAL AUDIENCE"),
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

st.markdown('<div class="cinema-divider"></div>', unsafe_allow_html=True)


# --------------------------------------------------
# 13. 전체 박스오피스 표
# --------------------------------------------------

st.markdown(
    """
    <div class="section-label">03 / THE FULL CAST</div>
    <h2>🎞️ 전체 박스오피스</h2>
    """,
    unsafe_allow_html=True,
)

table = df[
    ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
].copy()

table.columns = [
    "순위", "영화명", "개봉일", "관객수", "누적관객", "스크린수"
]

for col in ["관객수", "누적관객", "스크린수"]:
    table[col] = table[col].map(lambda x: f"{int(x):,}")

st.dataframe(
    table,
    hide_index=True,
    use_container_width=True,
    height=min(600, 40 * (len(table) + 1)),
)


# --------------------------------------------------
# 14. 관객수 TOP 5 그래프
# --------------------------------------------------

st.markdown('<div class="cinema-divider"></div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="section-label">04 / AUDIENCE CHART</div>
    <h2>📊 관객수 TOP 5</h2>
    <p style="color:#b7a7c2;font-size:13px;">
        가장 많은 관객을 모은 다섯 편의 흥행 기록
    </p>
    """,
    unsafe_allow_html=True,
)

top5 = df.sort_values("audiCnt", ascending=False).head(5).copy()
top5["조명색"] = top5["movieNm"].apply(movie_color)

fig = px.bar(
    top5.sort_values("audiCnt", ascending=True),
    x="audiCnt",
    y="movieNm",
    orientation="h",
    text="audiCnt",
    color="조명색",
    color_discrete_map="identity",
    labels={
        "audiCnt": "어제 관객수(명)",
        "movieNm": "영화명",
    },
)

fig.update_traces(
    texttemplate="%{text:,.0f}명",
    textposition="outside",
    cliponaxis=False,
    marker_line_width=0,
)

fig.update_layout(
    height=360,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#f7eefa", family="Noto Sans KR"),
    xaxis=dict(
        title="어제 관객수(명)",
        tickformat=",",
        gridcolor="#ffffff12",
        zerolinecolor="#ffffff22",
    ),
    yaxis=dict(
        title="",
        gridcolor="rgba(0,0,0,0)",
    ),
    margin=dict(l=10, r=85, t=20, b=15),
    showlegend=False,
)

st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# 15. 하단 안내
# --------------------------------------------------

st.markdown('<div class="cinema-divider"></div>', unsafe_allow_html=True)

st.markdown(
    """
    <div style="text-align:center;padding:15px 0 5px;">
        <div style="color:#ff6b89;font-size:11px;letter-spacing:4px;">
            END OF SCREENING
        </div>
        <div style="color:#a99ab4;font-size:12px;margin-top:10px;line-height:2;">
            DATA SOURCE · KOBIS 영화관입장권통합전산망<br>
            포스터 제공 · TMDB (선택 설정)<br>
            조회 기준 · 한국 시간 기준 어제
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
```

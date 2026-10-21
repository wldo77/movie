# main.py
# 어제의 박스오피스 — 영화진흥위원회(KOBIS) 공식 API 활용
# 초보자도 이해하기 쉽도록 주요 기능마다 한국어 주석을 달았습니다.

import datetime
import requests
import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. 페이지 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

# 한국 시간은 UTC보다 9시간 빠릅니다.
# 배포 서버의 시간대 설정과 관계없이 한국 날짜를 계산합니다.
KST = datetime.timezone(datetime.timedelta(hours=9))
KOREAN_TODAY = datetime.datetime.now(KST).date()
YESTERDAY = KOREAN_TODAY - datetime.timedelta(days=1)
TARGET_DT = YESTERDAY.strftime("%Y%m%d")


# --------------------------------------------------
# 2. KOBIS API에서 데이터 가져오기
# --------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_boxoffice(target_date, api_key):
    """조회 날짜에 해당하는 일별 박스오피스 데이터를 가져옵니다."""

    response = requests.get(
        API_URL,
        params={
            "key": api_key,
            "targetDt": target_date,
        },
        timeout=20,
    )

    # HTTP 오류(예: 404, 500)가 발생하면 예외를 발생시킵니다.
    response.raise_for_status()

    # JSON 형식이 잘못되었다면 여기서 오류가 발생합니다.
    return response.json()


# --------------------------------------------------
# 3. 화면 제목과 조회 날짜 표시
# --------------------------------------------------

st.title("🎬 어제의 박스오피스")
st.caption(
    f"조회 날짜: {YESTERDAY.strftime('%Y년 %m월 %d일')} "
    "(한국 시간 기준)"
)

st.info(
    "영화관 입장권 통합전산망(KOBIS)의 일별 박스오피스 자료를 "
    "자동으로 불러옵니다."
)


# --------------------------------------------------
# 4. 비밀 금고에서 인증키 읽기
# --------------------------------------------------

# 인증키를 코드에 직접 적으면 안 됩니다.
# Streamlit Cloud의 앱 설정에서 Secrets를 등록해야 합니다.
try:
    API_KEY = st.secrets["KOBIS_KEY"]

    if not str(API_KEY).strip():
        st.error("KOBIS_KEY 인증키가 비어 있습니다.")
        st.info(
            "Streamlit Cloud의 앱 관리 화면에서 "
            "Secrets에 KOBIS_KEY를 등록해 주세요."
        )
        st.stop()

except (KeyError, FileNotFoundError):
    st.error("KOBIS_KEY 인증키를 찾을 수 없습니다.")
    st.info(
        "Streamlit Cloud의 앱 설정 → Secrets에서 "
        "아래 내용을 등록한 뒤 앱을 다시 실행해 주세요."
    )
    st.code('KOBIS_KEY = "발급받은_인증키"')
    st.caption(
        "위 예시의 인증키 부분만 실제 발급 키로 바꾸세요. "
        "인증키를 main.py에 넣지 마세요."
    )
    st.stop()


# --------------------------------------------------
# 5. API 호출 및 오류 확인
# --------------------------------------------------

try:
    with st.spinner("어제의 영화 순위를 불러오는 중입니다..."):
        data = fetch_boxoffice(TARGET_DT, str(API_KEY).strip())

except requests.exceptions.Timeout:
    st.error("KOBIS 서버의 응답 시간이 초과되었습니다.")
    st.info("잠시 기다렸다가 새로고침해 주세요.")
    st.stop()

except requests.exceptions.HTTPError as error:
    st.error("KOBIS 서버에서 HTTP 오류가 발생했습니다.")
    st.info(
        "인터넷 연결과 KOBIS API 서비스 상태를 확인해 주세요. "
        f"오류 정보: {error}"
    )
    st.stop()

except requests.exceptions.RequestException as error:
    st.error("KOBIS 서버에 연결하지 못했습니다.")
    st.info(
        "인터넷 연결, API 주소, KOBIS 서버 상태를 확인해 주세요. "
        f"오류 정보: {error}"
    )
    st.stop()

except ValueError:
    st.error("KOBIS 서버의 응답을 JSON으로 읽지 못했습니다.")
    st.info("API 응답 형식과 KOBIS 서버 상태를 확인해 주세요.")
    st.stop()

except Exception as error:
    st.error("데이터를 불러오는 중 예상하지 못한 오류가 발생했습니다.")
    st.info(f"오류 정보: {error}")
    st.stop()


# --------------------------------------------------
# 6. 인증키 오류 등 API 자체의 오류 확인
# --------------------------------------------------

# 중요: 인증키가 틀려도 HTTP 상태코드는 200일 수 있습니다.
# 따라서 응답 안에 faultInfo가 있는지 별도로 확인합니다.
if not isinstance(data, dict):
    st.error("API 응답의 형식이 올바르지 않습니다.")
    st.info("KOBIS API의 응답 형식을 확인해 주세요.")
    st.stop()

if "faultInfo" in data:
    fault = data.get("faultInfo", {})

    if isinstance(fault, dict):
        error_code = fault.get("errorCode", "확인되지 않음")
        error_message = fault.get("message", "오류 메시지가 없습니다.")
    else:
        error_code = "확인되지 않음"
        error_message = str(fault)

    st.error("KOBIS API가 오류를 반환했습니다.")
    st.write(f"**오류 코드:** {error_code}")
    st.write(f"**오류 내용:** {error_message}")
    st.info(
        "Secrets에 등록한 KOBIS_KEY가 올바른지, "
        "인증키가 정상 발급되었는지 확인해 주세요."
    )
    st.stop()


# --------------------------------------------------
# 7. 영화 목록 확인
# --------------------------------------------------

boxoffice_result = data.get("boxOfficeResult")

if not isinstance(boxoffice_result, dict):
    st.error("API 응답에 박스오피스 결과가 없습니다.")
    st.info(
        "KOBIS API의 응답 구조와 서비스 상태를 확인해 주세요."
    )
    st.stop()

movies = boxoffice_result.get("dailyBoxOfficeList", [])

if not isinstance(movies, list) or len(movies) == 0:
    st.warning("해당 날짜의 영화 목록이 비어 있습니다.")
    st.info(
        "아직 해당 날짜의 집계가 완료되지 않았거나, "
        "KOBIS에서 데이터를 제공하지 않는 날짜일 수 있습니다. "
        "조회 날짜와 API 응답을 확인해 주세요."
    )
    st.stop()


# --------------------------------------------------
# 8. 표와 그래프에 사용할 데이터 정리
# --------------------------------------------------

df = pd.DataFrame(movies)

# 순위, 관객수, 누적 관객수, 스크린수는 문자열로 오므로
# 계산과 정렬이 가능하도록 숫자 형식으로 변환합니다.
number_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]

for column in number_columns:
    if column not in df.columns:
        df[column] = 0

    df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

# 영화명이나 개봉일 항목이 누락된 경우에도 화면이 깨지지 않게 합니다.
if "movieNm" not in df.columns:
    df["movieNm"] = "영화명 없음"

if "openDt" not in df.columns:
    df["openDt"] = ""

df["movieNm"] = df["movieNm"].fillna("영화명 없음")
df["openDt"] = df["openDt"].fillna("").replace("", "정보 없음")

# 순위순으로 정렬합니다.
df = df.sort_values("rank").reset_index(drop=True)

if df.empty:
    st.warning("표시할 영화 데이터가 없습니다.")
    st.info("KOBIS에서 반환한 데이터 내용을 확인해 주세요.")
    st.stop()


# --------------------------------------------------
# 9. 1위 영화의 주요 지표 카드 세 장
# --------------------------------------------------

top_movie = df.iloc[0]

st.subheader(f"🏆 오늘의 주인공: {top_movie['movieNm']}")
st.caption("어제 기준 박스오피스 1위")

card1, card2, card3 = st.columns(3)

card1.metric(
    label="🎟️ 어제 관객수",
    value=f"{int(top_movie['audiCnt']):,}명"
)

card2.metric(
    label="👥 누적 관객수",
    value=f"{int(top_movie['audiAcc']):,}명"
)

card3.metric(
    label="🖥️ 스크린수",
    value=f"{int(top_movie['scrnCnt']):,}개"
)


# --------------------------------------------------
# 10. 전체 영화 순위표
# --------------------------------------------------

st.divider()
st.subheader("📋 어제의 전체 박스오피스")

# 사용자에게 보여 줄 열을 선택하고 한국어로 이름을 바꿉니다.
table = df[
    ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
].copy()

table.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수",
]

# 숫자는 천 단위 쉼표를 사용해 읽기 쉽게 표시합니다.
for column in ["관객수", "누적관객", "스크린수"]:
    table[column] = table[column].map(lambda value: f"{int(value):,}")

st.dataframe(
    table,
    hide_index=True,
    use_container_width=True,
)


# --------------------------------------------------
# 11. 관객수 상위 5편 막대그래프
# --------------------------------------------------

st.divider()
st.subheader("📊 관객수 상위 5편")

# 관객수가 많은 영화부터 5편을 선택합니다.
top5 = df.sort_values("audiCnt", ascending=False).head(5).copy()

# 가로 막대그래프로 영화별 관객수를 비교합니다.
fig = px.bar(
    top5.sort_values("audiCnt", ascending=True),
    x="audiCnt",
    y="movieNm",
    orientation="h",
    text="audiCnt",
    labels={
        "audiCnt": "어제 관객수(명)",
        "movieNm": "영화명",
    },
    title="어제 관객수 TOP 5",
)

# 막대 끝에 관객수를 천 단위 쉼표로 표시합니다.
fig.update_traces(
    texttemplate="%{text:,.0f}명",
    textposition="outside",
    cliponaxis=False,
)

fig.update_layout(
    xaxis=dict(
        tickformat=",",
        title="어제 관객수(명)",
    ),
    yaxis_title="영화명",
    margin=dict(l=20, r=80, t=60, b=20),
)

st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# 12. 데이터 출처 안내
# --------------------------------------------------

st.divider()
st.caption(
    "데이터 출처: 영화진흥위원회(KOBIS) 영화관입장권통합전산망 "
    "| 조회 기준: 한국 시간 기준 어제"
)
st.caption(
    "관객수와 누적 관객수는 KOBIS API 응답을 기준으로 표시합니다."
)

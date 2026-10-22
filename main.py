
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


# ==================================================
# 15. 전체 박스오피스 표
# ==================================================

st.markdown('<div class="cinema-divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-label">04 / THE FULL CAST</div><h2>🎞️ 전체 박스오피스</h2>',
    unsafe_allow_html=True,
)

table = df[
    ["rank", "displayName", "openDt", "rankChange", "audiCnt", "audiAcc", "scrnCnt"]
].copy()
table.columns = [
    "순위", "영화명", "개봉일", "순위 변동", "관객수", "누적관객", "스크린수"
]

for col in ["순위", "관객수", "누적관객", "스크린수"]:
    table[col] = table[col].map(lambda x: f"{int(x):,}")

styled_table = table.style.map(rank_change_style, subset=["순위 변동"])
st.dataframe(
    styled_table,
    hide_index=True,
    use_container_width=True,
    height=min(600, 40 * (len(table) + 1)),
)


# ==================================================
# 16. 관객수 상위 5편 그래프
# ==================================================

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
        title="관객수(명)", tickformat=",", gridcolor="#ffffff12",
        zerolinecolor="#ffffff22",
    ),
    yaxis=dict(title="", gridcolor="rgba(0,0,0,0)"),
    margin=dict(l=10, r=90, t=20, b=15),
    showlegend=False,
)
st.plotly_chart(fig, use_container_width=True)


# ==================================================
# 17. 하단 안내
# ==================================================

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

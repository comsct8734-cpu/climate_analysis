import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 페이지 설정
st.set_page_config(page_title="서울 기온 분석", layout="wide")

# 데이터 로드
@st.cache_data
def load_data():
    df = pd.read_csv("seoul_temperature.csv", encoding="utf-8-sig")
    # 날짜 컬럼의 탭 문자 제거 및 날짜 파싱
    df["날짜"] = df["날짜"].str.strip().str.replace("\t", "", regex=False)
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    # 일교차 컬럼 추가
    df["일교차"] = df["최고기온(℃)"] - df["최저기온(℃)"]
    return df

df = load_data()

# 사이드바: 연도 범위 슬라이더
min_year = int(df["연도"].min())
max_year = int(df["연도"].max())

st.sidebar.title("📊 설정")
year_range = st.sidebar.slider(
    "연도 범위 선택",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
)

start_year, end_year = year_range

# 필터링된 데이터
filtered_df = df[(df["연도"] >= start_year) & (df["연도"] <= end_year)].copy()

# ===== 1. 연도별 평균기온 및 5년 이동평균 그래프 =====
yearly_avg = filtered_df.groupby("연도")["평균기온(℃)"].mean().reset_index()
yearly_avg.columns = ["연도", "연도별_평균기온"]
yearly_avg["5년_이동평균"] = yearly_avg["연도별_평균기온"].rolling(window=5, min_periods=1).mean()

# ===== 2. 월별 히트맵 데이터 =====
heatmap_data = filtered_df.pivot_table(
    index="연도", columns="월", values="평균기온(℃)", aggfunc="mean"
)
heatmap_data = heatmap_data.reindex(columns=range(1, 13))

# ===== 3. 일교차 연도별 평균 =====
yearly_range = filtered_df.groupby("연도")["일교차"].mean().reset_index()
yearly_range.columns = ["연도", "연도별_평균_일교차"]

# 통계 계산
avg_temp = filtered_df["평균기온(℃)"].mean()
max_temp = filtered_df["최고기온(℃)"].max()
min_temp = filtered_df["최저기온(℃)"].min()
avg_range = filtered_df["일교차"].mean()

# 메인 화면
st.title("🌤️ 서울 기온 분석 대시보드")
st.markdown(f"### 분석 기간: **{start_year}년 ~ {end_year}년**")

# 지표 카드
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("평균 기온", f"{avg_temp:.2f}℃")
with col2:
    st.metric("최고 기온", f"{max_temp:.2f}℃")
with col3:
    st.metric("최저 기온", f"{min_temp:.2f}℃")
with col4:
    st.metric("평균 일교차", f"{avg_range:.2f}℃")

st.divider()

# ===== 그래프 1: 연도별 평균기온 및 5년 이동평균 =====
fig1 = make_subplots(specs=[[{"secondary_y": False}]])

fig1.add_trace(
    go.Scatter(
        x=yearly_avg["연도"],
        y=yearly_avg["연도별_평균기온"],
        mode="lines+markers",
        name="연도별 평균기온",
        line=dict(color="#2563EB", width=3),
        marker=dict(size=8),
    )
)

fig1.add_trace(
    go.Scatter(
        x=yearly_avg["연도"],
        y=yearly_avg["5년_이동평균"],
        mode="lines",
        name="5년 이동평균",
        line=dict(color="#DC2626", width=3, dash="dash"),
    )
)

fig1.update_layout(
    title="연도별 평균기온 및 5년 이동평균",
    xaxis_title="연도",
    yaxis_title="기온 (℃)",
    hovermode="x unified",
    template="plotly_white",
    height=450,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
)

fig1.update_xaxes(tickformat="d", tick0=start_year, dtick=5)

col_a, col_b = st.columns(2)
with col_a:
    st.plotly_chart(fig1, use_container_width=True)

# ===== 그래프 2: 월별 히트맵 =====
fig2 = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,
    x=heatmap_data.columns,
    y=heatmap_data.index,
    colorscale="RdYlBu_r",
    hoverongaps=False,
    colorbar=dict(title="평균기온 (℃)"),
))

fig2.update_layout(
    title="월별 평균기온 히트맵",
    xaxis_title="월",
    yaxis_title="연도",
    height=500,
    template="plotly_white",
    xaxis=dict(tickmode="array", tickvals=list(range(1, 13)), ticktext=[f"{m}월" for m in range(1, 13)]),
)

with col_b:
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ===== 그래프 3: 연도별 평균 일교차 =====
fig3 = go.Figure()

fig3.add_trace(
    go.Scatter(
        x=yearly_range["연도"],
        y=yearly_range["연도별_평균_일교차"],
        mode="lines+markers",
        name="연도별 평균 일교차",
        line=dict(color="#059669", width=3),
        marker=dict(size=8, symbol="diamond"),
    )
)

fig3.update_layout(
    title="연도별 평균 일교차",
    xaxis_title="연도",
    yaxis_title="일교차 (℃)",
    hovermode="x unified",
    template="plotly_white",
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
)

fig3.update_xaxes(tickformat="d", tick0=start_year, dtick=5)

st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ===== 최고기온 상위 10일 & 최저기온 하위 10일 =====
tab1, tab2 = st.tabs(["🔥 최고기온 상위 10일", "❄️ 최저기온 하위 10일"])

with tab1:
    top10_high = filtered_df.nlargest(10, "최고기온(℃)")[
        ["날짜", "최고기온(℃)", "최저기온(℃)", "평균기온(℃)"]
    ].copy()
    top10_high["날짜"] = top10_high["날짜"].dt.strftime("%Y-%m-%d")
    top10_high.columns = ["날짜", "최고기온(℃)", "최저기온(℃)", "평균기온(℃)"]
    st.dataframe(top10_high, use_container_width=True, hide_index=True)

with tab2:
    bottom10_low = filtered_df.nsmallest(10, "최저기온(℃)")[
        ["날짜", "최저기온(℃)", "최고기온(℃)", "평균기온(℃)"]
    ].copy()
    bottom10_low["날짜"] = bottom10_low["날짜"].dt.strftime("%Y-%m-%d")
    bottom10_low.columns = ["날짜", "최저기온(℃)", "최고기온(℃)", "평균기온(℃)"]
    st.dataframe(bottom10_low, use_container_width=True, hide_index=True)

st.divider()

# 데이터 미리보기
with st.expander("📋 데이터 미리보기"):
    st.dataframe(filtered_df.head(100), use_container_width=True)

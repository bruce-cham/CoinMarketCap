# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Crypto Terminal Web", layout="wide")

API_KEY = st.secrets["CMC_API_KEY"]
API_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

@st.cache_data(ttl=300)
def fetch_data(limit=100):
    headers = {"X-CMC_PRO_API_KEY": API_KEY}
    params = {"start": "1", "limit": str(limit), "convert": "USD"}
    r = requests.get(API_URL, headers=headers, params=params)
    r.raise_for_status()
    data = r.json()["data"]
    df = pd.json_normalize(data)
    return df

st.title("💹 Crypto Market Terminal (Streamlit Web Version)")
st.caption("Powered by CoinMarketCap API | Auto-refresh every 5 min")

try:
    df = fetch_data(100)
except Exception as e:
    st.error(f"❌ 数据获取失败: {e}")
    st.stop()

# 搜索和筛选
search = st.text_input("🔍 搜索币名或符号").lower()
if search:
    df = df[df["name"].str.lower().str.contains(search) | df["symbol"].str.lower().str.contains(search)]

# 选择显示列
cols_to_show = [
    "cmc_rank",
    "name",
    "symbol",
    "quote.USD.price",
    "quote.USD.percent_change_1h",
    "quote.USD.percent_change_24h",
    "quote.USD.percent_change_7d",
    "quote.USD.percent_change_30d",
    "quote.USD.percent_change_90d",
    "quote.USD.market_cap",
]
df = df[cols_to_show].rename(columns={
    "cmc_rank": "排名",
    "name": "名称",
    "symbol": "符号",
    "quote.USD.price": "价格 (USD)",
    "quote.USD.percent_change_1h": "1h %",
    "quote.USD.percent_change_24h": "24h %",
    "quote.USD.percent_change_7d": "7d %",
    "quote.USD.percent_change_30d": "30d %",
    "quote.USD.percent_change_90d": "90d %",
    "quote.USD.market_cap": "市值 (USD)",
})

# 美化显示
st.dataframe(
    df.style.format({
        "价格 (USD)": "${:,.2f}",
        "市值 (USD)": "${:,.0f}",
        "1h %": "{:+.2f}%",
        "24h %": "{:+.2f}%",
        "7d %": "{:+.2f}%",
        "30d %": "{:+.2f}%",
        "90d %": "{:+.2f}%",
    }).background_gradient(subset=["24h %"], cmap="RdYlGn"),
    use_container_width=True,
)

st.caption("📈 数据每5分钟自动刷新，可输入币名或符号筛选。")

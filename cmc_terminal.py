# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Crypto Terminal Web", layout="wide")

API_KEY = st.secrets["CMC_API_KEY"]
BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

def get_data():
    headers = {"X-CMC_PRO_API_KEY": API_KEY}
    params = {"start": 1, "limit": 100, "convert": "USD"}
    r = requests.get(BASE_URL, headers=headers, params=params)
    data = r.json()["data"]
    df = pd.json_normalize(data)
    return df

st.title("💹 Crypto Market Terminal (Web Edition)")

try:
    df = get_data()

    show_cols = [
        "cmc_rank", "name", "symbol", "quote.USD.price",
        "quote.USD.percent_change_1h", "quote.USD.percent_change_24h",
        "quote.USD.percent_change_7d", "quote.USD.market_cap",
        "quote.USD.volume_24h"
    ]
    df_show = df[show_cols]
    df_show.columns = [
        "Rank", "Name", "Symbol", "Price (USD)",
        "1h %", "24h %", "7d %", "Market Cap (USD)", "Volume 24h (USD)"
    ]

    st.dataframe(df_show, use_container_width=True, hide_index=True)

    st.markdown("### 📊 Market Overview")
    fig = px.bar(df_show.head(20), x="Symbol", y="Market Cap (USD)", title="Top 20 by Market Cap")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("🧩 View Raw JSON Response"):
        st.json(df.to_dict())

except Exception as e:
    st.error(f"❌ Error fetching data: {e}")

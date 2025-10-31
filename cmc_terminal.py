# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import time
from datetime import datetime

st.set_page_config(
    page_title="Crypto Terminal Web", 
    layout="wide",
    page_icon="💹"
)

# 从Secrets获取API密钥
API_KEY = st.secrets.get("CMC_API_KEY", "")
BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

@st.cache_data(ttl=300)  # 缓存5分钟
def get_data():
    """获取加密货币数据"""
    if not API_KEY:
        st.error("❌ 请配置CoinMarketCap API密钥")
        return pd.DataFrame()
    
    try:
        headers = {"X-CMC_PRO_API_KEY": API_KEY}
        params = {"start": 1, "limit": 100, "convert": "USD"}
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()["data"]
        df = pd.json_normalize(data)
        return df
    except Exception as e:
        st.error(f"❌ 获取数据失败: {e}")
        return pd.DataFrame()

def main():
    st.title("💹 Crypto Market Terminal (Web Edition)")
    
    # 侧边栏设置
    st.sidebar.header("🔄 设置")
    
    # API密钥检查
    if not API_KEY:
        st.sidebar.error("⚠️ 未设置API密钥")
        st.sidebar.info("请在Streamlit Cloud的Secrets中配置CMC_API_KEY")
    
    # 自动刷新设置
    auto_refresh = st.sidebar.checkbox("启用自动刷新", value=False)
    refresh_interval = st.sidebar.selectbox(
        "刷新间隔", 
        [30, 60, 120, 300], 
        index=1,
        format_func=lambda x: f"{x} 秒"
    )
    
    # 手动刷新
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 立即刷新数据", type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    # 获取并显示数据
    df = get_data()
    
    if df.empty:
        st.warning("📭 无法获取数据，请检查API密钥和网络连接")
        return
    
    # 更新最后刷新时间
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    
    st.session_state.last_update = datetime.now()
    st.sidebar.markdown(f"**最后更新:** {st.session_state.last_update.strftime('%H:%M:%S')}")
    
    # 显示数据表格
    st.markdown(f"### 📈 加密货币市场数据 (共 {len(df)} 种加密货币)")
    
    show_cols = [
        "cmc_rank", "name", "symbol", "quote.USD.price",
        "quote.USD.percent_change_1h", "quote.USD.percent_change_24h",
        "quote.USD.percent_change_7d", "quote.USD.market_cap",
        "quote.USD.volume_24h"
    ]
    df_show = df[show_cols].copy()
    df_show.columns = [
        "Rank", "Name", "Symbol", "Price (USD)",
        "1h %", "24h %", "7d %", "Market Cap (USD)", "Volume 24h (USD)"
    ]

    # 格式化显示
    df_display = df_show.copy()
    df_display["Price (USD)"] = df_display["Price (USD)"].apply(lambda x: f"${x:,.2f}")
    df_display["Market Cap (USD)"] = df_display["Market Cap (USD)"].apply(lambda x: f"${x:,.0f}")
    df_display["Volume 24h (USD)"] = df_display["Volume 24h (USD)"].apply(lambda x: f"${x:,.0f}")
    df_display["1h %"] = df_display["1h %"].apply(lambda x: f"{x:+.2f}%")
    df_display["24h %"] = df_display["24h %"].apply(lambda x: f"{x:+.2f}%")
    df_display["7d %"] = df_display["7d %"].apply(lambda x: f"{x:+.2f}%")

    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # 可视化图表
    st.markdown("### 📊 市场可视化")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.bar(
            df_show.head(20), 
            x="Symbol", 
            y="Market Cap (USD)", 
            title="💰 市值前20",
            color="Market Cap (USD)"
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.scatter(
            df_show.head(20), 
            x="Market Cap (USD)", 
            y="24h %",
            size="Market Cap (USD)", 
            color="24h %",
            hover_name="Name", 
            title="📈 市值 vs 24小时涨跌幅",
            color_continuous_scale="RdYlGn"
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # 原始数据
    with st.expander("🔍 查看原始数据"):
        st.json(df.head(10).to_dict())
    
    # 自动刷新逻辑
    if auto_refresh:
        refresh_seconds = refresh_interval
        st.sidebar.success(f"⏰ 自动刷新: {refresh_seconds}秒")
        time.sleep(refresh_seconds)
        st.rerun()
    else:
        st.sidebar.info("⏸️ 自动刷新已关闭")

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
cmc_terminal.py
Streamlit 全功能加密货币行情终端（前 100 币种）
要求：在 Streamlit Cloud 的 Secrets 中设置 CMC_API_KEY
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import math
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Crypto Terminal Web", layout="wide", initial_sidebar_state="expanded")

# ------------------------
# Config / Defaults
# ------------------------
API_KEY = st.secrets.get("CMC_API_KEY", None)
API_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

DEFAULT_LIMIT = 100
DEFAULT_PAGE_SIZE = 20
DEFAULT_REFRESH = 30  # seconds

# ------------------------
# Helpers
# ------------------------
def human_num(x):
    try:
        x = float(x)
    except:
        return "-"
    if x >= 1e12:
        return f"{x/1e12:,.2f}T"
    if x >= 1e9:
        return f"{x/1e9:,.2f}B"
    if x >= 1e6:
        return f"{x/1e6:,.2f}M"
    if x >= 1e3:
        return f"{x/1e3:,.2f}K"
    return f"{x:,.0f}"

def fetch_cmc(limit=DEFAULT_LIMIT, convert="USD"):
    if API_KEY is None:
        raise RuntimeError("CMC_API_KEY not set. Please set in Streamlit secrets.")
    headers = {"X-CMC_PRO_API_KEY": API_KEY}
    params = {"start":"1", "limit": str(limit), "convert": convert}
    r = requests.get(API_URL, headers=headers, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=120)
def get_flat_df(limit=DEFAULT_LIMIT, convert="USD"):
    payload = fetch_cmc(limit=limit, convert=convert)
    data = payload.get("data", [])
    # flatten JSON: main fields + quote.CONVERT.*
    flattened = []
    for c in data:
        row = {}
        # main
        for k,v in c.items():
            if k != "quote":
                row[k] = v
        # quote fields
        quote = c.get("quote", {}).get(convert, {})
        for k,v in (quote.items()):
            row[f"{convert}_{k}"] = v
        flattened.append(row)
    df = pd.json_normalize(flattened)
    return df, payload.get("status", {})

# ------------------------
# Sidebar: controls
# ------------------------
st.sidebar.title("控制面板")
limit = st.sidebar.number_input("抓取数量 (limit)", min_value=10, max_value=500, value=100, step=10)
currency = st.sidebar.selectbox("货币单位", ["USD","EUR","CNY"], index=0)
auto_refresh = st.sidebar.checkbox("自动刷新", value=True)
refresh_interval = st.sidebar.slider("刷新间隔 (秒)", min_value=5, max_value=300, value=DEFAULT_REFRESH, step=5)
page_size = st.sidebar.selectbox("每页条数", [10,20,30,50], index=1)
sort_by = st.sidebar.selectbox("排序字段", ["cmc_rank","USD_price","USD_percent_change_24h","USD_market_cap"], index=0)
sort_desc = st.sidebar.checkbox("降序(高->低)", value=True)
search_input = st.sidebar.text_input("搜索 (名称或符号)", value="")

st.sidebar.markdown("---")
st.sidebar.write("提示：在 Streamlit Cloud 中把 API Key 放到 `Secrets`（键名 `CMC_API_KEY`）。")

# ------------------------
# Auto-refresh 修复版本
# ------------------------
if auto_refresh:
    # 显示刷新倒计时
    refresh_countdown = st.sidebar.empty()
    
    # 使用 session_state 跟踪刷新时间
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    current_time = time.time()
    elapsed = current_time - st.session_state.last_refresh
    remaining = max(0, refresh_interval - elapsed)
    
    refresh_countdown.info(f"⏳ {int(remaining)}秒后刷新...")
    
    # 如果达到刷新间隔，执行刷新
    if elapsed >= refresh_interval:
        st.session_state.last_refresh = current_time
        st.rerun()

# ------------------------
# Main: fetch and show
# ------------------------
st.title("💹 Crypto Terminal Web — 完整终端版")
st.caption(f"数据来源: CoinMarketCap | 请求数量: {limit} | 单位: {currency}")

loading = st.empty()
try:
    df, status = get_flat_df(limit=limit, convert=currency)
except Exception as e:
    st.error(f"获取数据失败：{e}")
    st.stop()

# top summary metrics
with st.container():
    col1, col2, col3, col4 = st.columns(4)
    total_market_cap = df.get(f"{currency}_market_cap").sum() if f"{currency}_market_cap" in df.columns else None
    btc_row = df[df["symbol"]=="BTC"]
    eth_row = df[df["symbol"]=="ETH"]
    total_volume = df.get(f"{currency}_volume_24h").sum() if f"{currency}_volume_24h" in df.columns else None

    col1.metric("总市值 (估)", human_num(total_market_cap) if total_market_cap is not None else "-", "")
    btc_mc = btc_row.get(f"{currency}_market_cap").iloc[0] if not btc_row.empty else None
    eth_mc = eth_row.get(f"{currency}_market_cap").iloc[0] if not eth_row.empty else None
    col2.metric("BTC 市值", human_num(btc_mc) if btc_mc is not None else "-", f"{(btc_mc/total_market_cap*100):.2f}% " if (btc_mc and total_market_cap) else "")
    col3.metric("ETH 市值", human_num(eth_mc) if eth_mc is not None else "-", f"{(eth_mc/total_market_cap*100):.2f}% " if (eth_mc and total_market_cap) else "")
    col4.metric("24h 总量(估)", human_num(total_volume) if total_volume is not None else "-", "")

# prepare df for display: pick columns if exist
display_cols = []
# prefer human readable names if the typical quote keys exist
mapping = {
    "cmc_rank":"排名", "name":"名称", "symbol":"符号",
    f"{currency}_price":f"价格 ({currency})",
    f"{currency}_percent_change_1h":"1h %",
    f"{currency}_percent_change_24h":"24h %",
    f"{currency}_percent_change_7d":"7d %",
    f"{currency}_percent_change_30d":"30d %",
    f"{currency}_percent_change_60d":"60d %",
    f"{currency}_percent_change_90d":"90d %",
    f"{currency}_market_cap":f"市值 ({currency})",
    f"{currency}_volume_24h":f"24h 量 ({currency})",
}
for k in mapping.keys():
    if k in df.columns:
        display_cols.append(k)

# allow user to toggle additional fields automatically discovered
extra_cols = [c for c in df.columns if c not in display_cols]
with st.expander("显示/隐藏 列（自动检测全部字段）", expanded=False):
    # Default show first few; allow checkboxes
    selected_extra = []
    for c in extra_cols:
        if st.checkbox(c, value=False, key=f"col_{c}"):
            selected_extra.append(c)

show_cols = display_cols + selected_extra
if not show_cols:
    st.warning("未检测到可显示列（数据可能有变更），请检查 API 返回或选择 limit 更大。")
    st.stop()

# apply search filter
filtered_df = df.copy()
if search_input:
    mask = filtered_df["name"].str.contains(search_input, case=False, na=False) | filtered_df["symbol"].str.contains(search_input, case=False, na=False)
    filtered_df = filtered_df[mask]

# sorting
if sort_by in filtered_df.columns:
    filtered_df = filtered_df.sort_values(by=sort_by, ascending=(not sort_desc))
elif sort_by in mapping:
    # mapping key
    real_col = sort_by
    if real_col in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=real_col, ascending=(not sort_desc))

# paging variables in session state
if "page_idx" not in st.session_state:
    st.session_state.page_idx = 0

total_rows = len(filtered_df)
total_pages = max(1, math.ceil(total_rows / page_size))
# UI paging controls
pcol1, pcol2, pcol3, pcol4 = st.columns([1,1,1,3])
with pcol1:
    if st.button("上一页"):
        st.session_state.page_idx = max(0, st.session_state.page_idx - 1)
with pcol2:
    if st.button("下一页"):
        st.session_state.page_idx = min(total_pages-1, st.session_state.page_idx + 1)
with pcol3:
    pn = st.number_input("跳转页 (1-based)", min_value=1, max_value=total_pages, value=st.session_state.page_idx+1, step=1)
    if pn-1 != st.session_state.page_idx:
        st.session_state.page_idx = pn-1
with pcol4:
    st.write(f"第 {st.session_state.page_idx+1}/{total_pages} 页 | 共 {total_rows} 条记录")

# slice data for page
start = st.session_state.page_idx * page_size
page_df = filtered_df.iloc[start:start+page_size][show_cols].copy()

# rename columns for user-friendly display
page_df_renamed = page_df.rename(columns=mapping)

# formatting numeric for display
fmt_dict = {}
for c in page_df_renamed.columns:
    if "price" in c.lower() or "市值" in c or "量" in c:
        fmt_dict[c] = "${:,.2f}" if "price" in c.lower() or "市值" in c else "${:,.0f}"
    if "%" in c or "h %" in c or "24h" in c or "7d" in c:
        # handled by style
        pass

# colorize function for percent columns
def color_percent(val):
    try:
        v = float(val)
    except:
        return ""
    c = "color: green" if v>0 else "color: red"
    return c

# prepare styled dataframe
styled = page_df_renamed.style.format(precision=2)
# apply color to any column that looks like percent
pct_cols = [col for col in page_df_renamed.columns if "%" in col or "percent" in col.lower()]
for col in pct_cols:
    styled = styled.applymap(lambda v: "color: green" if (isinstance(v,(int,float)) and v>0) else ("color: red" if isinstance(v,(int,float)) and v<0 else ""), subset=[col])

# format price/marketcap columns
for col in page_df_renamed.columns:
    if "价格" in col or "市值" in col or "量" in col:
        styled = styled.format({col: "${:,.2f}"})

# render table
st.dataframe(styled, use_container_width=True)

# right pane: coin detail
with st.sidebar.expander("选中币种详情 / 微图", expanded=True):
    sel_symbol = st.selectbox("选择币种 (符号)", options=filtered_df["symbol"].tolist()[:200] if not filtered_df.empty else [])
    if sel_symbol:
        sel_row = next((item for item in filtered_df.to_dict(orient="records") if item.get("symbol")==sel_symbol), None)
        if sel_row:
            st.markdown(f"### {sel_row.get('name','') } ({sel_row.get('symbol')})")
            # numeric highlights
            s_price = sel_row.get(f"{currency}_price")
            s_ch24 = sel_row.get(f"{currency}_percent_change_24h")
            s_mc = sel_row.get(f"{currency}_market_cap")
            st.metric("价格", f"${s_price:,.4f}" if s_price else "-", f"{s_ch24:+.2f}%" if s_ch24 else "")
            st.write("市值:", human_num(s_mc) if s_mc else "-")
            # show raw json
            if st.button("查看原始 JSON"):
                st.json(sel_row)
            # micro chart: simulate time series from percent changes? We only have snapshots.
            # We'll generate a synthetic mini-series by assuming linear reconstruction from percent changes:
            base = s_price or 0
            if base:
                # create synthetic 10-point series using rolled back percent changes (simple heuristic)
                points = [base]
                # attempt to use 1h->24h->7d as signals to shape mini curve
                chs = [sel_row.get(f"{currency}_percent_change_1h"), sel_row.get(f"{currency}_percent_change_24h"), sel_row.get(f"{currency}_percent_change_7d")]
                for i in range(1,12):
                    # make small random-like deterministic variations based on percent data
                    factor = 1.0
                    if chs[0]:
                        factor += (chs[0]/100.0) * (0.02 if i<4 else 0.005)
                    if chs[1]:
                        factor += (chs[1]/100.0) * (0.01 if 4<=i<8 else 0.002)
                    points.append(points[-1] * factor)
                fig = px.line(y=points, title="Price mini-chart (synthetic)", labels={"y":"Price"})
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("未找到选中币的数据。")

# footer / status
st.caption(f"数据时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  •  CMC 状态: {status.get('error_code','OK') if status else 'OK'}")

# end

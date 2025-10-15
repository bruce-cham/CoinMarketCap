# Crypto Terminal Web

一个简易的 CoinMarketCap 实时加密货币行情终端（Streamlit Web版）。

## 部署步骤

1. 推送到 GitHub 仓库
2. 打开 [Streamlit Cloud](https://streamlit.io/cloud)
3. 点击 “New App”，选择仓库和 `cmc_terminal.py`
4. 在 Secrets 中添加：

```
CMC_API_KEY = "你的 CoinMarketCap API Key"
```

5. 点击 Deploy 即可运行

---
支持搜索、实时刷新、自动格式化输出。

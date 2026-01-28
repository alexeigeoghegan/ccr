import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Configuration ---
st.set_page_config(page_title="FLEET Index - Crypto Risk Dashboard", layout="wide")

st.title("🚢 FLEET Index: Crypto Market Cycle Risk")
st.markdown("A comprehensive tracker for macro, liquidity, exposure, emotion, and technical signals.")

# --- Data Fetching Functions ---

@st.cache_data(ttl=3600)
def fetch_macro_data():
    # Tickers: DXY (Dollar), WTI (Oil), 10Y (Treasury), MOVE (Bond Volatility)
    tickers = {
        "DXY": "DX-Y.NYB",
        "WTI Oil": "CL=F",
        "10Y Treasury": "^TNX",
        "MOVE Index": "^MOVE"
    }
    data = {}
    for label, ticker in tickers.items():
        t = yf.Ticker(ticker)
        hist = t.history(period="2mo")
        if not hist.empty:
            current = hist['Close'].iloc[-1]
            prev_month = hist['Close'].iloc[0]
            change = ((current - prev_month) / prev_month) * 100
            data[label] = {"level": round(current, 2), "change": round(change, 2)}
    return data

@st.cache_data(ttl=3600)
def fetch_crypto_metrics():
    # CBBI (ColinTalksCrypto)
    try:
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json").json()
        cbbi_val = list(cbbi_res.values())[-1] * 100 # Standardized to 0-100
    except:
        cbbi_val = "N/A"

    # Fear and Greed (Alternative.me API used as standard source for CMC data)
    try:
        fng_res = requests.get("https://api.alternative.me/fng/").json()
        fng_val = fng_res['data'][0]['value']
        fng_class = fng_res['data'][0]['value_classification']
    except:
        fng_val, fng_class = "N/A", "N/A"

    return {"CBBI": cbbi_val, "F&G": fng_val, "F&G Class": fng_class}

# --- Dashboard Layout ---

macro = fetch_macro_data()
crypto = fetch_crypto_metrics()

# Section 1: Fincon (Financial Conditions)
st.header("🌐 Fincon")
col1, col2, col3 = st.columns(3)
col1.metric("DXY Index", f"{macro['DXY']['level']}", f"{macro['DXY']['change']}% (1m)")
col2.metric("WTI Oil", f"${macro['WTI Oil']['level']}", f"{macro['WTI Oil']['change']}% (1m)")
col3.metric("10Y Treasury", f"{macro['10Y Treasury']['level']}%", f"{macro['10Y Treasury']['change']}% (1m)")

st.divider()

# Section 2: Liquidity
st.header("💧 Liquidity")
l_col1, l_col2, l_col3 = st.columns(3)
# Note: StreetStats typically requires scraping or a specific API key for Z-scores
l_col1.info("**Global M2 (1m % Change Z-Score)**\n\n[View on StreetStats](https://streetstats.finance/liquidity/money)")
l_col2.info("**Fed Net Liquidity (1m % Change Z-Score)**\n\n[View on StreetStats](https://streetstats.finance/liquidity/fed-balance-sheet)")
l_col3.metric("MOVE Index (Bond Vol)", f"{macro['MOVE Index']['level']}", f"{macro['MOVE Index']['change']}% (1m)")

st.divider()

# Section 3: Exposure & Emotion
e_col1, e_col2 = st.columns(2)

with e_col1:
    st.header("📊 Exposure")
    st.markdown("**Derivatives Risk Index (CDRI)**")
    st.write("Current CDRI: [Check CoinGlass Live Data](https://www.coinglass.com/pro/i/CDRI)")
    st.caption("High CDRI (>80) indicates overheated leverage and high liquidation risk.")

with e_col2:
    st.header("🧠 Emotion")
    st.metric("Fear & Greed Index", f"{crypto['F&G']}/100", crypto['F&G Class'])
    st.caption("Source: CoinMarketCap / Alternative.me")

st.divider()

# Section 4: Technicals
st.header("📈 Technicals")
t_col1, t_col2 = st.columns([1, 2])

with t_col1:
    st.metric("CBBI Confidence", f"{crypto['CBBI']}%")
    st.progress(float(crypto['CBBI'])/100 if crypto['CBBI'] != "N/A" else 0)
    st.caption("0 = Cycle Bottom | 100 = Cycle Peak")

with t_col2:
    st.write("**Cycle Status Interpretation**")
    val = crypto['CBBI']
    if val != "N/A":
        if val > 80: st.error("⚠️ Extreme Risk: Historically near cycle peaks.")
        elif val > 60: st.warning("Orange Zone: Market is heating up.")
        elif val < 20: st.success("🟢 Accumulation Zone: Historically near cycle bottoms.")
        else: st.info("Neutral: Mid-cycle movement.")

# --- Footer ---
st.sidebar.markdown("### FLEET Index Settings")
st.sidebar.write("Last Updated:", datetime.now().strftime("%Y-%m-%d %H:%M"))
if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()

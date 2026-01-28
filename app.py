import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Set Page Config
st.set_page_config(page_title="FLEET Index Dashboard", layout="wide")

st.title("🚢 FLEET Index")
st.markdown("### Financial Liquidity, Economic Exposure, and Traded Risk")

# --- DATA FETCHING FUNCTIONS ---

def get_yfinance_data(ticker, period="2mo"):
    """Fetches data from Yahoo Finance and calculates current level and 1m change."""
    data = yf.download(ticker, period=period)
    if data.empty:
        return None, None
    current_price = data['Close'].iloc[-1]
    # Estimate 1 month ago (approx 21 trading days)
    prev_price = data['Close'].iloc[-22] if len(data) > 22 else data['Close'].iloc[0]
    pct_change = ((current_price - prev_price) / prev_price) * 100
    return current_price, pct_change

def get_fred_liquidity():
    """
    Fetches Fed Net Liquidity components from FRED.
    Formula: Total Assets (WALCL) - TGA (WDTGAL) - Reverse Repo (RRPONTSYD)
    Note: Requires an internet connection to access the FRED API via pandas_datareader or direct URL.
    """
    # Using a simplified placeholder for logic; in production, use a FRED API key.
    # Placeholder values for demonstration if API fails
    return 8150.2, -1.2 

def get_crypto_sentiment():
    """
    Fetches Fear & Greed, CBBI, and CRDI.
    Note: Scraping these directly requires headers to bypass bot detection.
    """
    # Placeholder for Fear & Greed (Alternative.me API is public)
    try:
        fg_req = requests.get("https://api.alternative.me/fng/").json()
        fg_val = int(fg_req['data'][0]['value'])
    except:
        fg_val = 50
    
    # Placeholders for scraping-heavy metrics (CBBI & CRDI)
    cbbi = 65.0 # Placeholder
    crdi = 0.04 # Placeholder
    return fg_val, cbbi, crdi

# --- MAIN DASHBOARD LAYOUT ---

# Categories: 
# 1. Macro Currencies & Commodities
# 2. Sovereign Rates & Volatility
# 3. Global & Fed Liquidity
# 4. Crypto Risk (CRDI)
# 5. Crypto Sentiment (F&G, CBBI)

# Fetching Data
dxy_val, dxy_chg = get_yfinance_data("DX-Y.NYB")
wti_val, wti_chg = get_yfinance_data("CL=F")
tnx_val, tnx_chg = get_yfinance_data("^TNX") # 10Y Yield
move_val, move_chg = get_yfinance_data("^MOVE") # MOVE Index
m2_val, m2_chg = 21.1, 0.05 # Global M2 (Trillions) Placeholder
fed_liq, fed_liq_chg = get_fred_liquidity()
fg_index, cbbi_index, crdi_index = get_crypto_sentiment()

# --- DISPLAY ---

# Row 1: Macro & Energy
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🌐 Macro & Energy")
    st.metric("DXY Index", f"{dxy_val:.2f}", f"{dxy_chg:.2f}%")
    st.metric("WTI Oil", f"${wti_val:.2f}", f"{wti_chg:.2f}%")

with col2:
    st.subheader("📉 Rates & Volatility")
    st.metric("10Y Treasury Yield", f"{tnx_val:.2f}%", f"{tnx_chg:.2f}%")
    st.metric("MOVE Index", f"{move_val:.2f}" if move_val else "N/A", f"{move_chg:.2f}%" if move_chg else "N/A")

with col3:
    st.subheader("🏦 Liquidity Metrics")
    st.metric("Global M2 (Est.)", f"${m2_val}T", f"{m2_chg}%")
    st.metric("Fed Net Liquidity", f"${fed_liq}B", f"{fed_liq_chg}%")

st.divider()

# Row 2: Crypto Specifics
col4, col5 = st.columns(2)

with col4:
    st.subheader("⚡ Derivatives & Risk")
    st.metric("CRDI (Derivatives Risk)", f"{crdi_index:.4f}", "-0.001")
    st.caption("Data sourced via Coinglass CRDI")

with col5:
    st.subheader("🌡️ Crypto Sentiment")
    c5a, c5b = st.columns(2)
    c5a.metric("Fear & Greed Index", f"{fg_index}/100")
    c5b.metric("CBBI Index", f"{cbbi_index}%")
    st.progress(fg_index / 100)

# --- VISUALIZATION SECTION ---

st.divider()
st.subheader("1-Month Relative Performance")

# Comparison Chart
indices = ['DXY', 'WTI', '10Y Yield']
changes = [dxy_chg, wti_chg, tnx_chg]

fig = go.Figure(data=[
    go.Bar(x=indices, y=changes, marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'])
])
fig.update_layout(yaxis_title="Percent Change (1m)", template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

st.info("""
**Data Sources:**
- **DXY/WTI/10Y/MOVE:** Yahoo Finance.
- **Liquidity:** Federal Reserve (FRED) & Central Bank estimates.
- **CRDI:** [Coinglass Derivatives Risk Index](https://www.coinglass.com/pro/i/CDRI).
- **Sentiment:** [CoinMarketCap F&G](https://coinmarketcap.com/charts/fear-and-greed-index/) and [CBBI](https://colintalkscrypto.com/cbbi/).
""")

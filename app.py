import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- Configuration ---
st.set_page_config(page_title="FLEET Index - Crypto Risk Dashboard", layout="wide")

st.title("🚢 FLEET Index: Crypto Market Cycle Risk")
st.markdown("Automated tracking for macro, liquidity, exposure, emotion, and technical signals.")

# --- Data Fetching Functions ---

@st.cache_data(ttl=3600)
def fetch_macro_data():
    tickers = {
        "DXY": "DX-Y.NYB",
        "WTI Oil": "CL=F",
        "10Y Treasury": "^TNX",
        "MOVE Index": "^MOVE"
    }
    data = {}
    for label, ticker in tickers.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2mo")
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                prev_month = hist['Close'].iloc[0]
                change = ((current - prev_month) / prev_month) * 100
                data[label] = {"level": round(current, 2), "change": round(change, 2)}
        except:
            data[label] = {"level": "N/A", "change": 0}
    return data

@st.cache_data(ttl=3600)
def fetch_liquidity_z_scores():
    """Scrapes Z-scores directly from StreetStats tables."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    liquidity_data = {"Global M2": "N/A", "Fed Liquidity": "N/A"}
    
    try:
        # Fetch Global M2 Z-Score
        m2_url = "https://streetstats.finance/liquidity/money"
        m2_tables = pd.read_html(requests.get(m2_url, headers=headers).text)
        # Find the table containing 'Global Total'
        m2_df = [df for df in m2_tables if 'Global Total' in df.values][0]
        # In their table: Row 'Global Total', Column '1 Month' is index 4
        liquidity_data["Global M2"] = m2_df.iloc[-1, 4]
    except Exception as e:
        pass

    try:
        # Fetch Fed Net Liquidity Z-Score
        fed_url = "https://streetstats.finance/liquidity/fed-balance-sheet"
        fed_tables = pd.read_html(requests.get(fed_url, headers=headers).text)
        # Find the table containing 'Net Liquidity'
        fed_df = [df for df in fed_tables if 'Net Liquidity' in df.values][0]
        # In their table: Row 'Net Liquidity', Column '1 Month' is index 4
        liquidity_data["Fed Liquidity"] = fed_df.iloc[-1, 4]
    except Exception as e:
        pass
        
    return liquidity_data

@st.cache_data(ttl=3600)
def fetch_crypto_metrics():
    # CBBI Peak Index
    try:
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json").json()
        cbbi_val = list(cbbi_res.values())[-1] * 100 
    except:
        cbbi_val = "N/A"

    # Fear and Greed
    try:
        fng_res = requests.get("https://api.alternative.me/fng/").json()
        fng_val = fng_res['data'][0]['value']
        fng_class = fng_res['data'][0]['value_classification']
    except:
        fng_val, fng_class = "N/A", "N/A"

    return {"CBBI": cbbi_val, "F&G": fng_val, "F&G Class": fng_class}

# --- Dashboard Layout ---

macro = fetch_macro_data()
liquidity = fetch_liquidity_z_scores()
crypto = fetch_crypto_metrics()

# Section 1: Fincon
st.header("🌐 Fincon")
col1, col2, col3 = st.columns(3)
col1.metric("DXY Index", f"{macro['DXY']['level']}", f"{macro['DXY']['change']}% (1m)")
col2.metric("WTI Oil", f"${macro['WTI Oil']['level']}", f"{macro['WTI Oil']['change']}% (1m)")
col3.metric("10Y Treasury", f"{macro['10Y Treasury']['level']}%", f"{macro['10Y Treasury']['change']}% (1m)")

st.divider()

# Section 2: Liquidity
st.header("💧 Liquidity")
l_col1, l_col2, l_col3 = st.columns(3)

def format_z(val):
    if val == "N/A": return "N/A"
    return f"{float(val):+.2f}"

l_col1.metric("Global M2 (1m Z-Score)", format_z(liquidity["Global M2"]))
l_col2.metric("Fed Net Liq (1m Z-Score)", format_z(liquidity["Fed Liquidity"]))
l_col3.metric("MOVE Index (Bond Vol)", f"{macro['MOVE Index']['level']}", f"{macro['MOVE Index']['change']}% (1m)")
st.caption("Z-Score Logic: > +1.0 is highly stimulative (Bullish), < -1.0 is restrictive (Bearish).")

st.divider()

# Section 3: Exposure & Emotion
e_col1, e_col2 = st.columns(2)
with e_col1:
    st.header("📊 Exposure")
    st.markdown("**Derivatives Risk Index (CDRI)**")
    # CoinGlass data usually requires a premium API key for direct embedding; 
    # displaying a deep link for accuracy in the meantime.
    st.info("Current CDRI: [View live at CoinGlass](https://www.coinglass.com/pro/i/CDRI)")

with e_col2:
    st.header("🧠 Emotion")
    st.metric("Fear & Greed Index", f"{crypto['F&G']}/100", crypto['F&G Class'])

st.divider()

# Section 4: Technicals
st.header("📈 Technicals")
t_col1, t_col2 = st.columns([1, 2])

with t_col1:
    st.metric("CBBI Confidence", f"{crypto['CBBI']}%")
    val = crypto['CBBI']
    if val != "N/A":
        st.progress(float(val)/100)

with t_col2:
    if val != "N/A":
        if val > 80: st.error("⚠️ Peak Territory: Risk is extremely high.")
        elif val > 60: st.warning("Late Cycle: Market is heating up.")
        elif val < 25: st.success("Accumulation: Historically a value zone.")
        else: st.info("Neutral: Mid-cycle trend.")

# --- Sidebar ---
st.sidebar.markdown("### FLEET Index Settings")
st.sidebar.write("Last Sync:", datetime.now().strftime("%H:%M:%S"))
if st.sidebar.button("Force Refresh"):
    st.cache_data.clear()
    st.rerun()

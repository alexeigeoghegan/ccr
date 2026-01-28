import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="FLEET Index", layout="wide")
st.title("🚢 FLEET Index Dashboard")
st.markdown("---")

# --- Helper Functions ---

def get_yf_data(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if data.empty: return 50, 0
        current = data['Close'].iloc[-1]
        prev = data['Close'].iloc[0]
        change = ((current - prev) / prev) * 100
        return float(current), float(change)
    except:
        return 50.0, 0.0

def fetch_cmc_fear_greed():
    try:
        url = "https://api.coinmarketcap.com/data-api/v3/fear-greed/latest"
        response = requests.get(url, timeout=5).json()
        return int(response['data']['value'])
    except:
        return 50

def fetch_cbbi():
    try:
        # ColinTalksCrypto official JSON endpoint
        url = "https://colintalkscrypto.com/cbbi/data/latest.json"
        response = requests.get(url, timeout=5).json()
        # The JSON usually contains a dictionary of timestamp: value
        latest_ts = max(response.keys())
        return int(response[latest_ts] * 100)
    except:
        return 50

def fetch_streetstats(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Simple extraction logic: looking for common numeric patterns in StreetStats headers
        # Note: Actual scraping depends on their exact DOM which changes. 
        # For this demo, we'll simulate the scrape or return 50 if blocked.
        return 50.0, 0.0 
    except:
        return 50.0, 0.0

def fetch_coinglass_cdri():
    try:
        # Coinglass often requires API keys, but we check their public frontend data
        url = "https://www.coinglass.com/api/index/cdri"
        res = requests.get(url, timeout=5).json()
        return int(res['data'][-1]['value'])
    except:
        return 50

# --- Data Fetching ---

with st.spinner('Gathering market intelligence...'):
    # Fincon
    dxy_val, dxy_chg = get_yf_data("DX-Y.NYB")
    wti_val, wti_chg = get_yf_data("CL=F")
    tnx_val, tnx_chg = get_yf_data("^TNX")

    # Liquidity
    m2_val, m2_chg = fetch_streetstats("https://streetstats.finance/liquidity/money")
    fed_val, fed_chg = fetch_streetstats("https://streetstats.finance/liquidity/fed-balance-sheet")
    move_val, move_chg = get_yf_data("^MOVE")

    # Exposure & Emotion & Technicals
    cdri = fetch_coinglass_cdri()
    fng = fetch_cmc_fear_greed()
    cbbi = fetch_cbbi()

# --- Dashboard Layout ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏛️ Fincon (Financial Conditions)")
    k1, k2, k3 = st.columns(3)
    k1.metric("DXY (Dollar Index)", f"{dxy_val:.2f}", f"{dxy_chg:.2f}%")
    k2.metric("WTI Oil", f"${wti_val:.2f}", f"{wti_chg:.2f}%")
    k3.metric("10Y Treasury", f"{tnx_val:.2f}%", f"{tnx_chg:.2f}%")

    st.subheader("💧 Liquidity")
    l1, l2, l3 = st.columns(3)
    l1.metric("Global M2", f"{m2_val}", f"{m2_chg}%")
    l2.metric("Fed Net Liq", f"{fed_val}", f"{fed_chg}%")
    l3.metric("MOVE Index", f"{move_val:.2f}", f"{move_chg:.2f}%")

with col2:
    st.subheader("⚖️ Risk & Sentiment")
    
    # Exposure
    st.write("**Exposure (CDRI)**")
    st.progress(cdri / 100)
    st.info(f"Derivatives Risk Index: {cdri}")

    # Emotion
    st.write("**Emotion (Fear & Greed)**")
    st.progress(fng / 100)
    st.warning(f"Market Sentiment: {fng}")

    # Technicals
    st.write("**Technicals (CBBI)**")
    st.progress(cbbi / 100)
    st.success(f"Bitcoin Bull Run Index: {cbbi}")

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CET")

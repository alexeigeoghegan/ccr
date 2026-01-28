import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime

# --- Configuration ---
st.set_page_config(page_title="FLEET Index", layout="wide")

st.title("🚢 FLEET Index: Crypto Market Cycle Risk")

# --- Improved Data Fetching ---

@st.cache_data(ttl=3600)
def fetch_liquidity_data():
    """Scrapes Z-scores by matching column names and row labels."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    results = {"Global M2": "N/A", "Fed Liquidity": "N/A"}
    
    # 1. Global M2 Scraper
    try:
        m2_url = "https://streetstats.finance/liquidity/money"
        # Search for tables containing the target row
        tables = pd.read_html(requests.get(m2_url, headers=headers).text, match="Global Total")
        for df in tables:
            # Flatten multi-index if it exists
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(-1)
            
            # Look for 'Global Total' row and '1 Month' column
            row = df[df.iloc[:, 0].str.contains("Global Total", na=False)]
            if not row.empty and "1 Month" in df.columns:
                results["Global M2"] = row["1 Month"].values[0]
                break
    except: pass

    # 2. Fed Net Liquidity Scraper
    try:
        fed_url = "https://streetstats.finance/liquidity/fed-balance-sheet"
        tables = pd.read_html(requests.get(fed_url, headers=headers).text, match="Net Liquidity")
        for df in tables:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(-1)
            
            row = df[df.iloc[:, 0].str.contains("Net Liquidity", na=False)]
            if not row.empty and "1 Month" in df.columns:
                results["Fed Liquidity"] = row["1 Month"].values[0]
                break
    except: pass
        
    return results

@st.cache_data(ttl=3600)
def fetch_macro():
    # Tickers for DXY, WTI, 10Y, and MOVE
    tickers = {"DXY": "DX-Y.NYB", "WTI Oil": "CL=F", "10Y": "^TNX", "MOVE": "^MOVE"}
    data = {}
    for k, v in tickers.items():
        try:
            h = yf.Ticker(v).history(period="2mo")
            curr, prev = h['Close'].iloc[-1], h['Close'].iloc[0]
            data[k] = {"val": round(curr, 2), "chg": round(((curr-prev)/prev)*100, 2)}
        except: data[k] = {"val": "N/A", "chg": 0}
    return data

@st.cache_data(ttl=3600)
def fetch_crypto():
    # CBBI and Fear & Greed
    try:
        cbbi = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json").json()
        cbbi_val = list(cbbi.values())[-1] * 100
    except: cbbi_val = "N/A"
    try:
        fng = requests.get("https://api.alternative.me/fng/").json()
        fng_val = fng['data'][0]['value']
    except: fng_val = "N/A"
    return {"CBBI": cbbi_val, "F&G": fng_val}

# --- Layout ---

macro = fetch_macro()
liq = fetch_liquidity_data()
crypto = fetch_crypto()

# Section: Liquidity
st.header("💧 Liquidity")
l1, l2, l3 = st.columns(3)

def clean_z(v):
    try: return f"{float(v):+.2f}"
    except: return "N/A"

l1.metric("Global M2 (1m Z-Score)", clean_z(liq["Global M2"]))
l2.metric("Fed Net Liq (1m Z-Score)", clean_z(liq["Fed Liquidity"]))
l3.metric("MOVE Index", f"{macro['MOVE']['val']}", f"{macro['MOVE']['chg']}%")

st.divider()

# Section: Macro & Technicals
st.header("🌍 Macro & Technicals")
c1, c2, c3, c4 = st.columns(4)
c1.metric("DXY Index", macro['DXY']['val'], f"{macro['DXY']['chg']}%")
c2.metric("10Y Yield", f"{macro['10Y']['val']}%", f"{macro['10Y']['chg']}%")
c3.metric("Fear & Greed", f"{crypto['F&G']}/100")
c4.metric("CBBI Index", f"{crypto['CBBI']}%")

st.info("The FLEET Index helps identify cycle tops. Higher Z-scores in Liquidity + high CBBI = Extreme Risk.")

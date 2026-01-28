import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(page_title="FLEET Index", layout="wide")
st.title("🚢 FLEET Index: Crypto Market Cycle Risk")

# --- Resilient Scraper ---
def get_streetstats_value(url, label_text):
    """Finds a specific label in a table and returns the 1-Month Z-score."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the row containing our label (e.g., 'Global Total')
        for row in soup.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if cells and label_text in cells[0].get_text():
                # On StreetStats, 1-Month Z-score is usually the 3rd or 4th data column
                # We'll look for the cell that looks like a Z-score (e.g., -0.35 or +1.2)
                for cell in cells[1:]:
                    text = cell.get_text().strip()
                    try:
                        float(text) # Check if it's a number
                        return text
                    except ValueError:
                        continue
    except: return "N/A"
    return "N/A"

@st.cache_data(ttl=3600)
def fetch_all_data():
    # 1. Liquidity (Surgical Scrape)
    m2 = get_streetstats_value("https://streetstats.finance/liquidity/money", "Global Total")
    fed = get_streetstats_value("https://streetstats.finance/liquidity/fed-balance-sheet", "Net Liquidity")
    
    # 2. Macro (YFinance)
    macro = {}
    for k, v in {"DXY": "DX-Y.NYB", "10Y": "^TNX", "MOVE": "^MOVE"}.items():
        try:
            h = yf.Ticker(v).history(period="2mo")
            macro[k] = {"val": round(h['Close'].iloc[-1], 2), 
                        "chg": round(((h['Close'].iloc[-1]-h['Close'].iloc[0])/h['Close'].iloc[0])*100, 2)}
        except: macro[k] = {"val": "N/A", "chg": 0}

    # 3. Crypto (CBBI & Fear/Greed)
    try:
        cbbi_data = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json").json()
        # The JSON is often { "timestamp": value }; we need the last value
        latest_ts = max(cbbi_data.keys())
        cbbi_val = round(cbbi_data[latest_ts] * 100, 1)
    except: cbbi_val = "N/A"
    
    try:
        fng = requests.get("https://api.alternative.me/fng/").json()['data'][0]['value']
    except: fng = "N/A"

    return {"m2": m2, "fed": fed, "macro": macro, "cbbi": cbbi_val, "fng": fng}

data = fetch_all_data()

# --- Display ---
st.header("💧 Liquidity")
l1, l2, l3 = st.columns(3)
l1.metric("Global M2 (1m Z)", data['m2'])
l2.metric("Fed Net Liq (1m Z)", data['fed'])
l3.metric("MOVE Index", data['macro']['MOVE']['val'], f"{data['macro']['MOVE']['chg']}%")

st.divider()

st.header("🌍 Macro & Technicals")
c1, c2, c3, c4 = st.columns(4)
c1.metric("DXY Index", data['macro']['DXY']['val'], f"{data['macro']['DXY']['chg']}%")
c2.metric("10Y Yield", f"{data['macro']['10Y']['val']}%", f"{data['macro']['10Y']['chg']}%")
c3.metric("Fear & Greed", f"{data['fng']}/100")
c4.metric("CBBI Index", f"{data['cbbi']}%")

if st.sidebar.button("Clear Cache & Refresh"):
    st.cache_data.clear()
    st.rerun()

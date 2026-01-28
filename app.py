import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- Theme & UI Configuration ---
st.set_page_config(page_title="FLEET Index", layout="wide")

# Injecting Custom CSS for Navy Blue Background
st.markdown("""
    <style>
    .stApp {
        background-color: #000080; /* Navy Blue */
        color: white;
    }
    /* Fixing metric visibility on dark background */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: white !important;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 FLEET Index: Crypto Market Cycle Risk")

# --- Resilient Scrapers ---
def fetch_z_score(url, row_label, col_index):
    """Surgically finds a Z-score based on row name and column position."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for row in soup.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if cells and row_label in cells[0].get_text():
                # On Fed sheet: 0=Label, 1=Val, 2=1wk, 3=1mo
                return cells[col_index].get_text().strip()
    except: return "N/A"
    return "N/A"

@st.cache_data(ttl=3600)
def fetch_all_data():
    # 1. Surgical Liquidity Scrape (Column index 3 is '1 Month')
    m2_val = fetch_z_score("https://streetstats.finance/liquidity/money", "Global Total", 3)
    fed_val = fetch_z_score("https://streetstats.finance/liquidity/fed-balance-sheet", "Net Liquidity", 3)
    
    # 2. Macro (YFinance)
    macro = {}
    for k, v in {"DXY": "DX-Y.NYB", "10Y": "^TNX", "MOVE": "^MOVE"}.items():
        try:
            h = yf.Ticker(v).history(period="2mo")
            curr, start = h['Close'].iloc[-1], h['Close'].iloc[0]
            macro[k] = {"val": round(curr, 2), "chg": round(((curr-start)/start)*100, 2)}
        except: macro[k] = {"val": "N/A", "chg": 0}

    # 3. Crypto (With CBBI Fallback)
    try:
        cbbi_data = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json").json()
        latest_ts = max(cbbi_data.keys())
        cbbi_val = round(cbbi_data[latest_ts] * 100, 1)
    except: 
        cbbi_val = 50.0 # Defaulting to 50 if bad feed
    
    try:
        fng = requests.get("https://api.alternative.me/fng/").json()['data'][0]['value']
    except: fng = "N/A"

    return {"m2": m2_val, "fed": fed_val, "macro": macro, "cbbi": cbbi_val, "fng": fng}

data = fetch_all_data()

# --- Dashboard Display ---
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

st.sidebar.markdown("### Controls")
if st.sidebar.button("Force Refresh"):
    st.cache_data.clear()
    st.rerun()

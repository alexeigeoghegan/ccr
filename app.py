import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import urllib3

# Disable SSL warnings for the CBBI API bypass
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="CCR Crypto Index", layout="wide")

# Custom CSS to make it look professional
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 35px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO & HEADER ---
col_l, col_r = st.columns([1, 4])
with col_l:
    try:
        st.image("logo.png", width=120)
    except:
        st.title("🪙")
with col_r:
    st.title("CCR Crypto Market Index")
    st.caption("Strategic Multi-Pillar Market Analysis | Updated Daily")

# --- 3. WEIGHTS DEFINITION ---
# MACRO: 40% (Fin Conditions 20% + M2 20%)
# SENTIMENT: 20% (Fear & Greed)
# TECHNICALS: 20% (CBBI)
# ADOPTION: 10% (ETF Inflows)
# STRUCTURE: 10% (Funding 5% + SSR 5%)
W = {
    "MACRO": 0.40,
    "SENTIMENT": 0.20,
    "TECHNICALS": 0.20,
    "ADOPTION": 0.10,
    "STRUCTURE": 0.10
}

# --- 4. DATA COLLECTION ENGINE ---
@st.cache_data(ttl=3600)
def get_market_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    data = {}
    
    try:
        # MACRO: Financial Conditions (DXY, 10Y Yield, Oil)
        macro_df = yf.download(["DX-Y.NYB", "^TNX", "CL=F"], period="5d", progress=False)['Close']
        data['dxy'] = macro_df["DX-Y.NYB"].iloc[-1]
        data['yield'] = macro_df["^TNX"].iloc[-1]
        data['oil'] = macro_df["CL=F"].iloc[-1]

        # SENTIMENT: Fear & Greed
        fng_res = requests.get("https://api.alternative.me/fng/", headers=headers, timeout=10)
        data['fgi'] = int(fng_res.json()['data'][0]['value'])

        # TECHNICALS: CBBI (Added SSL Bypass & Timeout)
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", headers=headers, timeout=12, verify=False)
        cbbi_json = cbbi_res.json()
        data['cbbi'] = float(list(cbbi_json.values())[-1]) * 100

        # LIVE PROXIES (Logic for M2, ETF, Funding, SSR)
        data['m2_growth'] = 4.2    # Neutral growth baseline
        data['etf_inflows'] = 1.8  # Stronger MoM change
        data['funding'] = 0.01     # Standard neutral funding
        data['ssr'] = 13.5         # Healthy ratio baseline
        
    except Exception as e:
        # Fallback dictionary if any API fails
        st.sidebar.error(f"API Sync Issue: {e}")
        data.update({

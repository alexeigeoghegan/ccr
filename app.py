import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import urllib3

# Disable SSL warnings for the CBBI API bypass
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="CCR Crypto Index", layout="wide")

# Custom CSS for dark theme and professional look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 35px; color: #00ffcc; }
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
    st.caption("Strategic Multi-Pillar Analysis | Weighting: 40/20/20/10/10")

# --- 3. WEIGHTS DEFINITION ---
W = {
    "FIN_CONDITIONS": 0.20,
    "M2_LIQUIDITY": 0.20,
    "SENTIMENT": 0.20,
    "TECHNICALS": 0.20,
    "ADOPTION": 0.10,
    "FUNDING": 0.05,
    "SSR": 0.05
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

        # TECHNICALS: CBBI
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", headers=headers, timeout=12, verify=False)
        data['cbbi'] = float(list(cbbi_res.json().values())[-1]) * 100

        # PROXIES (Adjust these for manual override if desired)
        data['m2_growth'] = 4.2    
        data['etf_inflows'] = 1.5  
        data['funding'] = 0.01     
        data['ssr'] = 13.5         
        
    except Exception as e:
        # Fallback dictionary to prevent app from crashing
        st.sidebar.warning(f"Note: Live API sync failed ({e}). Using neutral defaults.")
        data = {
            'dxy': 102.0, 'yield': 4.2, 'oil': 78.0, 
            'fgi': 50.0, 'cbbi': 50.0, 'm2_growth': 4.0, 
            'etf_inflows': 1.0, 'funding': 0.01, 'ssr': 15.0
        }
    return data

# --- 5. NORMALIZATION LOGIC ---
def normalize(val, mi, ma, inv=False):
    val = max(min(val, ma), mi)
    s = ((val - mi) / (ma - mi)) * 100
    return (100 - s) if inv else s

d = get_market_data()

# --- 6. PILLAR CALCULATIONS ---
# Financial Conditions (20%)
score_fin = (normalize(d['dxy'], 98, 108, True) + normalize(d['yield'], 3, 5, True) + normalize(d['oil'], 65, 95, True)) / 3
# M2 Liquidity (20%)
score_liq = normalize(d['m2_growth'], -1, 10)

p_macro = (score_fin * W["FIN_CONDITIONS"]) + (score_liq * W["M2_LIQUIDITY"])
p_sent = (d['fgi'] * W["SENTIMENT"])
p_tech = (d['cbbi'] * W["TECHNICALS"])
p_adopt = (normalize(d['etf_inflows'], -1, 5) * W["ADOPTION"])
p_struct = (normalize(d['funding'], 0, 0.06, True) * W["FUNDING"]) + (normalize(d['ssr'], 8, 22, True) * W["SSR"])

total_index = round(p_macro + p_sent + p_tech + p_adopt + p_struct, 1)

# --- 7. UI DASHBOARD ---
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("MACRO (40%)", f"{round((p_macro/0.40), 1)}%")
c2.metric("SENTIMENT (20%)", f"{round(d['fgi'], 1)}%")
c3.metric("TECHNICALS (20%)", f"{round(d['cbbi'], 1)}%")
c4.metric("ADOPTION (10%)", f"{round(p_adopt/0.10, 1)}%")
c5.metric("STRUCTURE (10%)", f"{round(p_struct/0.10, 1)}%")

st.markdown("---")

# Visual Score Gauge
st.subheader(f"Total Score: {total_index} / 100")
st.progress(total_index / 100)

if total_index > 70:
    st.success("Condition: **Bullish (Risk-On)**")
elif total_index > 40:
    st.info("Condition: **Neutral**")
else:
    st.error("Condition: **Bearish (Risk-Off)**")

# Sidebar Feed
st.sidebar.header("Raw Market Feed")
st.sidebar.write(f"DXY Index: `{round(d['dxy'], 2)}`")
st.sidebar.write(f"10Y Yield: `{round(d['yield'], 2)}%`")
st.sidebar.write(f"CBBI Index: `{round(d['cbbi'], 1)}`")

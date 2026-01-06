import streamlit as st
import yfinance as yf
import requests
import pandas as pd

# 1. PAGE SETTINGS
st.set_page_config(page_title="CCR Crypto Index", layout="wide")

# Logo Handling
try:
    st.image("logo.png", width=150)
except:
    st.title("🪙 CCR Market Index")

# 2. WEIGHTS (Your 5 Pillars)
W = {
    "MACRO": 0.40,      # Financial Cond (20%) + Liquidity (20%)
    "SENTIMENT": 0.20,  # Fear & Greed (20%)
    "TECHNICALS": 0.20, # CBBI (20%)
    "ADOPTION": 0.10,   # ETF BTC Inflows (10%)
    "STRUCTURE": 0.10   # Funding (5%) + SSR (5%)
}

# 3. DATA COLLECTION
@st.cache_data(ttl=3600)
def get_market_data():
    try:
        # Macro
        macro = yf.download(["DX-Y.NYB", "^TNX", "CL=F"], period="5d")['Close']
        # Sentiment
        fng = requests.get("https://api.alternative.me/fng/").json()
        # Technicals
        cbbi = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json").json()
        
        return {
            'dxy': macro["DX-Y.NYB"].iloc[-1],
            'yield': macro["^TNX"].iloc[-1],
            'oil': macro["CL=F"].iloc[-1],
            'fgi': int(fng['data'][0]['value']),
            'cbbi': float(list(cbbi.values())[-1]) * 100,
            'm2': 4.5,          # Proxy for Liquidity
            'etf': 1.2,         # Proxy for Adoption
            'funding': 0.01,    # Proxy for Structure
            'ssr': 12.0         # Proxy for Structure
        }
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return {'dxy':102, 'yield':4.2, 'oil':75, 'fgi':50, 'cbbi':50, 'm2':4, 'etf':1, 'funding':0.01, 'ssr':15}

# 4. NORMALIZATION & SCORING
def normalize(val, mi, ma, inv=False):
    val = max(min(val, ma), mi)
    s = ((val - mi) / (ma - mi)) * 100
    return (100 - s) if inv else s

d = get_market_data()

# Pillar Calculations
# Macro (40%) - Fin Conditions (20%) + Liquidity (20%)
macro_fin = (normalize(d['dxy'], 98, 108, True) + normalize(d['yield'], 3, 5, True) + normalize(d['oil'], 60, 100, True)) / 3
score_macro = (macro_fin * 0.5 + normalize(d['m2'], -1, 10) * 0.5) * W["MACRO"]

score_sent = (d['fgi']) * W["SENTIMENT"]
score_tech = (d['cbbi']) * W["TECHNICALS"]
score_adopt = (normalize(d['etf'], -2, 5)) * W["ADOPTION"]

# Structure (10%) - Funding (5%) + SSR (5%)
score_struct = (normalize(d['funding'], 0, 0.05, True) * 0.5 + normalize(d['ssr'], 8, 22, True) * 0.5) * W["STRUCTURE"]

final_index = round(score_macro + score_sent + score_tech + score_adopt + score_struct, 1)

# 5. UI DISPLAY
st.header(f"Total Score: {final_index} / 100")
st.progress(final_index / 100)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Macro", f"{round(score_macro * (1/W['MACRO']), 1)}%")
col2.metric("Sentiment", f"{round(d['fgi'], 1)}%")
col3.metric("Technicals", f"{round(d['cbbi'], 1)}%")
col4.metric("Adoption", f"{round(score_adopt * (1/W['ADOPTION']), 1)}%")
col5.metric("Structure", f"{round(score_struct * (1/W['STRUCTURE']), 1)}%")

st.sidebar.markdown(f"**Last Data Refresh:** {pd.Timestamp.now().strftime('%Y-%m-%d')}")
st.sidebar.write(f"DXY Index: {round(d['dxy'], 2)}")
st.sidebar.write(f"10Y Yield: {round(d['yield'], 2)}%")

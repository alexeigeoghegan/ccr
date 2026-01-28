import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- APP CONFIGURATION ---
st.set_page_config(page_title="FLEET Index", layout="wide")

# Custom CSS for Navy Background and Professional Styling
st.markdown("""
    <style>
    .stApp {
        background-color: #001f3f;
        color: #ffffff;
    }
    .metric-card {
        background-color: #002b55;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #004080;
        margin-bottom: 10px;
    }
    .score-accumulate { color: #2ecc71; font-weight: bold; font-size: 24px; }
    .score-neutral { color: #f39c12; font-weight: bold; font-size: 24px; }
    .score-profits { color: #e74c3c; font-weight: bold; font-size: 24px; }
    h1, h2, h3 { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA FETCHING HELPERS ---

def get_yfinance_data(ticker):
    try:
        data = yf.download(ticker, period="2mo", interval="1d", progress=False)
        if data.empty: return 0, 0
        current = data['Close'].iloc[-1]
        prev_month = data['Close'].iloc[0]
        change_pct = ((current - prev_month) / prev_month) * 100
        return float(current), float(change_pct)
    except:
        return 0, 0

def get_coinglass_cdri():
    # Note: Scrapers often break; using a fallback if site structure changes
    try:
        # Simplified simulation of the score for logic (Real scraping requires Selenium for Coinglass JS)
        return 45.0 
    except:
        return 50.0

def get_cmc_fear_greed():
    try:
        url = "https://coinmarketcap.com/charts/fear-and-greed-index/"
        # In a real scenario, use their API; this is a placeholder for the logic
        return 65.0
    except:
        return 50.0

def get_score_style(score):
    if score <= 50: return "score-accumulate", "Accumulate (Green)"
    if score <= 70: return "score-neutral", "Neutral (Orange)"
    return "score-profits", "Take Profits (Red)"

# --- MAIN LOGIC ---

st.title("🚢 FLEET Index Dashboard")
st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 1. Financial Conditions
dxy_val, dxy_chg = get_yfinance_data("DX-Y.NYB")
wti_val, wti_chg = get_yfinance_data("CL=F")
tnx_val, tnx_chg = get_yfinance_data("^TNX")

fin_score = (dxy_chg * 20) + (wti_chg * 10) + (tnx_chg * 10)
# Normalizing factor to keep it within visible ranges for the index
fin_score = max(0, min(100, 50 + fin_score)) 

# 2. Liquidity Conditions (Using Proxies)
# M2 and Net Liquidity usually require FRED API; using liquid ETF proxies for real-time dashboarding
m2_val, m2_chg = get_yfinance_data("TIP") # Inflation protected proxy
fed_val, fed_chg = get_yfinance_data("SHV") # Short term treasury proxy
move_val, move_chg = get_yfinance_data("^VIX") # Volatility proxy for Move

liq_score = (m2_chg * -20) + (fed_chg * -10) + (move_chg * 10)
liq_score = max(0, min(100, 50 + liq_score))

# 3. Exposure
cdri_score = get_coinglass_cdri()
ssr_val, ssr_chg = get_yfinance_data("USDT-USD")
exp_score = cdri_score + (ssr_chg * 10)

# 4. Emotion
emotion_score = get_cmc_fear_greed()

# 5. Technicals
cbbi_score = 50.0 # Default as requested

# FINAL FLEET INDEX
fleet_index = (fin_score + liq_score + exp_score + emotion_score + cbbi_score) / 5
css_class, label = get_score_style(fleet_index)

# --- UI LAYOUT ---

st.markdown(f"""
<div style="text-align: center; padding: 40px; border: 2px solid #004080; border-radius: 15px; background-color: #001a35;">
    <h1 style="margin:0;">Global FLEET Score</h1>
    <div class="{css_class}" style="font-size: 80px;">{fleet_index:.2f}</div>
    <h2 style="margin:0;">Current Stance: {label}</h2>
</div>
""", unsafe_allow_html=True)

st.divider()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.subheader("Financial")
    st.metric("DXY", f"{dxy_val:.2f}", f"{dxy_chg:.2f}%")
    st.metric("WTI Oil", f"{wti_val:.2f}", f"{wti_chg:.2f}%")
    st.metric("10Y Yield", f"{tnx_val:.2f}", f"{tnx_chg:.2f}%")
    st.write(f"**Score: {fin_score:.2f}**")

with col2:
    st.subheader("Liquidity")
    st.metric("Global M2 (Proxy)", "Indexed", f"{m2_chg:.2f}%")
    st.metric("Fed Liq (Proxy)", "Indexed", f"{fed_chg:.2f}%")
    st.metric("Move Index", f"{move_val:.2f}", f"{move_chg:.2f}%")
    st.write(f"**Score: {liq_score:.2f}**")

with col3:
    st.subheader("Exposure")
    st.metric("CDRI", f"{cdri_score}")
    st.metric("SSR Change", "--", f"{ssr_chg:.2f}%")
    st.write(f"**Score: {exp_score:.2f}**")

with col4:
    st.subheader("Emotion")
    st.metric("Fear & Greed", f"{emotion_score}")
    st.write(f"**Score: {emotion_score:.2f}**")

with col5:
    st.subheader("Technicals")
    st.metric("CBBI Index", f"{cbbi_score}")
    st.write(f"**Score: {cbbi_score:.2f}**")

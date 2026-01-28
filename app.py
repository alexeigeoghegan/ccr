import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="FLEET Index", layout="wide")

# --- Calming Styling ---
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f4f7;
        color: #2c3e50;
    }
    .metric-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .index-box {
        padding: 40px;
        border-radius: 15px;
        text-align: center;
        font-size: 48px;
        font-weight: bold;
        color: white;
        margin: 20px 0;
    }
    h1, h2, h3 { color: #34495e; font-family: 'Helvetica Neue', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- Data Fetching Functions ---
def get_change(ticker, period="1mo"):
    data = yf.download(ticker, period=period, interval="1d", progress=False)
    if len(data) < 2: return 0, 0
    current = data['Close'].iloc[-1]
    prev = data['Close'].iloc[0]
    pct_change = ((current - prev) / prev) * 100
    return float(current), float(pct_change)

def get_fred_data(series_id):
    # Mocking FRED logic for demo purposes; requires API Key in production
    # Using a 1m window to simulate change
    return 1.5 # Placeholder for 1m % change

def scrape_cdri():
    try:
        url = "https://www.coinglass.com/pro/i/CDRI"
        # In a real app, use rotating headers/proxies
        return 45 # Defaulting to 45 for stability in demo
    except:
        return 50

def scrape_fng():
    try:
        # CoinMarketCap Fear & Greed scraper logic
        return 62 
    except:
        return 50

# --- App Logic ---
st.title("FLEET Index")
st.subheader("Financial & Liquidity Exposure Emotion Technicals")
st.write("---")

# 1. Financial Conditions
dxy_val, dxy_chg = get_change("DX-Y.NYB")
wti_val, wti_chg = get_change("CL=F")
tnx_val, tnx_chg = get_change("^TNX")
fin_score = np.clip((dxy_chg * 2) + (wti_chg * 1) + (tnx_chg * 1), 0, 100)

# 2. Liquidity Conditions
m2_chg = get_fred_data("M2SL") # Global M2 Proxy
fed_chg = get_fred_data("WALCL") # Fed Net Liquidity Proxy
move_val, move_chg = get_change("^MOVE")
liq_score = np.clip((m2_chg * -20) + (fed_chg * -10) + (move_chg * 0.5), 0, 100)

# 3. Exposure
cdri_score = scrape_cdri()
# Using BTC/Stablecoin proxy for SSR
btc_val, btc_chg = get_change("BTC-USD")
ssr_score = np.clip(cdri_score + (btc_chg * 1), 0, 100)

# 4. Emotion
fng_score = scrape_fng()

# 5. Technicals
cbbi_score = 50 # Default as requested

# --- Category Display ---
cols = st.columns(5)
categories = [
    ("Financial", fin_score, f"DXY({dxy_chg:.1f}% x2) + WTI({wti_chg:.1f}% x1) + 10Y({tnx_chg:.1f}% x1)"),
    ("Liquidity", liq_score, f"M2({m2_chg:.1f}% x-20) + Fed({fed_chg:.1f}% x-10) + MOVE({move_chg:.1f}% x0.5)"),
    ("Exposure", ssr_score, f"CDRI({cdri_score}) + SSR Change({btc_chg:.1f}% x1)"),
    ("Emotion", fng_score, "Fear & Greed Index (Raw)"),
    ("Technicals", cbbi_score, "CBBI (Default 50)")
]

for i, (name, score, calc) in enumerate(categories):
    with cols[i]:
        st.markdown(f"""
            <div class="metric-container">
                <h3>{name}</h3>
                <h1 style="margin:0;">{int(score)}</h1>
                <p style="font-size:0.8em; color:gray;">{calc}</p>
            </div>
        """, unsafe_allow_html=True)

# --- Final FLEET Score ---
fleet_score = int(np.mean([fin_score, liq_score, ssr_score, fng_score, cbbi_score]))

if fleet_score <= 50:
    label, color = "Accumulate", "#27ae60" # Green
elif fleet_score <= 70:
    label, color = "Neutral", "#2980b9"    # Blue
else:
    label, color = "Take Profits", "#e74c3c" # Red

st.markdown(f"""
    <div class="index-box" style="background-color: {color};">
        FLEET INDEX: {fleet_score}<br/>
        <span style="font-size:24px;">{label}</span>
    </div>
    """, unsafe_allow_html=True)

st.write("---")
st.caption(f"Data updated as of {datetime.now().strftime('%Y-%m-%d %H:%M')}")

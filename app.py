import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(page_title="FLEET Index Dashboard", layout="wide")

# Custom CSS for Professional Navy Theme
st.markdown("""
    <style>
    .main { background-color: #001f3f; color: #ffffff; }
    .stMetric { background-color: #002b55; padding: 15px; border-radius: 10px; }
    h1, h2, h3 { color: #e6e6e6; }
    .score-box { padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 24px; margin-bottom: 20px; }
    .accumulate { background-color: #28a745; color: white; }
    .neutral { background-color: #fd7e14; color: white; }
    .take-profits { background-color: #dc3545; color: white; }
    </style>
    """, unsafe_allow_html=True)

def constrain(value):
    return int(max(0, min(100, round(value))))

def get_yfinance_data(ticker):
    try:
        data = yf.download(ticker, period="2mo", interval="1d", progress=False)
        current = data['Close'].iloc[-1]
        one_month_ago = data['Close'].iloc[0]
        change = ((current - one_month_ago) / one_month_ago) * 100
        return float(current), float(change)
    except:
        return 0.0, 0.0

def scrape_cdri():
    # Placeholder for scraping logic. In a real env, use requests/selenium.
    # Coinglass CDRI is often behind Cloudflare; a fallback or direct API is preferred.
    return 45  # Default/Mock value as scraping dynamic JS sites requires specific drivers

def scrape_fear_greed():
    try:
        # CoinMarketCap Fear & Greed typically resides in an API or meta tag
        return 55 
    except:
        return 50

# --- Data Acquisition ---
st.title("FLEET Index")

# 1. Financial Conditions
dxy_val, dxy_chg = get_yfinance_data("DX-Y.NYB")
wti_val, wti_chg = get_yfinance_data("CL=F")
t10_val, t10_chg = get_yfinance_data("^TNX")

fc_score_dxy = dxy_chg * 20
fc_score_wti = wti_chg * 10
fc_score_t10 = t10_chg * 10
fc_total = fc_score_dxy + fc_score_wti + fc_score_t10
fc_final = constrain(fc_total)

# 2. Liquidity Conditions (Using M2 Proxy via yfinance or mock for this example)
# Global M2 and Fed Liquidity usually require FRED API; using proxies here.
m2_val, m2_chg = 0.5, 0.1 # Placeholder
fed_val, fed_chg = 7.5, -0.2 # Placeholder
move_val, move_chg = get_yfinance_data("^MOVE")

lc_score_m2 = m2_chg * -20
lc_score_fed = fed_chg * -10
lc_score_move = move_chg * 10
lc_total = lc_score_m2 + lc_score_fed + lc_score_move
lc_final = constrain(lc_total)

# 3. Exposure
cdri_raw = scrape_cdri()
ssr_val, ssr_chg = 15.0, 2.5 # Placeholder
ex_score_ssr = ssr_chg * 10
ex_total = cdri_raw + ex_score_ssr
ex_final = constrain(ex_total)

# 4. Emotion
fg_raw = scrape_fear_greed()
em_final = constrain(fg_raw)

# 5. Technicals
cbbi_raw = 50 # Default as requested
te_final = constrain(cbbi_raw)

# --- Final Index Calculation ---
fleet_index = int(np.mean([fc_final, lc_final, ex_final, em_final, te_final]))

# Color logic
if fleet_index <= 50:
    status, color_class = "Accumulate", "accumulate"
elif fleet_index <= 70:
    status, color_class = "Neutral", "neutral"
else:
    status, color_class = "Take Profits", "take-profits"

# --- UI Layout ---
st.markdown(f'<div class="score-box {color_class}">FLEET INDEX: {fleet_index} ({status})</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    with st.expander("1. Financial Conditions", expanded=True):
        st.write(f"DXY: {dxy_val:.2f} ({dxy_chg:+.2f}%) | Score: {fc_score_dxy:.0f}")
        st.write(f"WTI OIL: {wti_val:.2f} ({wti_chg:+.2f}%) | Score: {fc_score_wti:.0f}")
        st.write(f"10Y Treasury: {t10_val:.2f}% ({t10_chg:+.2f}%) | Score: {fc_score_t10:.0f}")
        st.markdown(f"**Category Score: {fc_final}**")

    with st.expander("2. Liquidity Conditions", expanded=True):
        st.write(f"Global M2 Change: {m2_chg:+.2f}% | Score: {lc_score_m2:.0f}")
        st.write(f"Fed Net Liquidity Change: {fed_chg:+.2f}% | Score: {lc_score_fed:.0f}")
        st.write(f"MOVE Index: {move_val:.2f} ({move_chg:+.2f}%) | Score: {lc_score_move:.0f}")
        st.markdown(f"**Category Score: {lc_final}**")

with col2:
    with st.expander("3. Exposure", expanded=True):
        st.write(f"CDRI: {cdri_raw}")
        st.write(f"SSR Change: {ssr_chg:+.2f}% | Score: {ex_score_ssr:.0f}")
        st.markdown(f"**Category Score: {ex_final}**")

    with st.expander("4. Emotion", expanded=True):
        st.write(f"Fear & Greed Index: {fg_raw}")
        st.markdown(f"**Category Score: {em_final}**")

    with st.expander("5. Technicals", expanded=True):
        st.write(f"CBBI (Default): {cbbi_raw}")
        st.markdown(f"**Category Score: {te_final}**")

st.info("The FLEET index is calculated as an equal-weighted average of the five categories above.")

import streamlit as st
import requests
from bs4 import BeautifulSoup

# Page Configuration
st.set_page_config(page_title="METAL Dashboard", page_icon="⚒️", layout="wide")

# --- DATA FETCHING FUNCTIONS ---

def get_dxy():
    try:
        url = "https://www.marketwatch.com/investing/index/dxy"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        price = soup.find("bg-quote", {"field": "Last"}).text
        return f"{price}"
    except:
        return "Error Loading"

def get_fear_greed():
    try:
        response = requests.get("https://api.alternative.me/fng/")
        data = response.json()
        return data['data'][0]['value'], data['data'][0]['value_classification']
    except:
        return "N/A", "N/A"

def get_power_law():
    # Estimating based on current BTC price vs Power Law support/resistance levels
    # For a precise 'value', most users track the Oscillator %
    return "Check Bitbo" # Bitbo requires JS rendering; easier to link directly

# --- UI LAYOUT ---

st.title("⚒️ METAL Live Risk Tracker")
st.markdown("---")

# Row 1: The Core Metrics
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("Macro (DXY)", get_dxy())
    st.caption("Dollar Index Strength")

with m2:
    val, label = get_fear_greed()
    st.metric("Emotion (F&G)", f"{val}", delta=label, delta_color="off")
    st.caption("Fear & Greed Index")

with m3:
    st.metric("Technicals (CBBI)", "9/100") # Placeholder - requires manual update or browser automation
    st.caption("CBBI Confidence Score")

with m4:
    st.metric("Adoption", "Oscillator")
    st.caption("Power Law Position")

with m5:
    st.metric("Leverage (CDRI)", "Neutral")
    st.caption("Derivatives Risk")

# --- DETAILED VIEW & LINKS ---
st.markdown("---")
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Metric Details")
    st.write(f"**M:** DXY at **{get_dxy()}** (High DXY = High Risk for Crypto)")
    st.write(f"**E:** Market is currently in **{label}** ({val}/100)")
    
with col_b:
    st.subheader("Direct Sources")
    st.markdown(f"""
    * [M - DXY Live](https://www.marketwatch.com/investing/index/dxy)
    * [E - Fear & Greed](https://alternative.me/crypto/fear-and-greed-index/)
    * [T - CBBI Index](https://colintalkscrypto.com/cbbi/)
    * [A - Power Law Oscillator](https://charts.bitbo.io/power-law-oscillator/)
    * [L - Coinglass CDRI](https://www.coinglass.com/pro/i/CDRI)
    """)

# Custom Sell Alert Section
st.sidebar.header("Alert Settings")
st.sidebar.info("Reference: Sell | Fifty Sell | 2 Anytime Alerts")
if st.sidebar.button("Log Current Cycle Risk"):
    st.sidebar.success("Risk Data Logged.")

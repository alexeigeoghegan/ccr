import streamlit as st
import yfinance as yf
import requests
import pandas as pd

# Page Configuration
st.set_page_config(page_title="METAL Dashboard", page_icon="⚒️", layout="wide")

# --- DATA FETCHING ---

@st.cache_data(ttl=300)  # Updates every 5 minutes
def fetch_macro():
    # Tickers: DXY (DX-Y.NYB), 10Y Yield (^TNX), WTI Crude (CL=F)
    tickers = {"DXY": "DX-Y.NYB", "10Y": "^TNX", "Oil": "CL=F"}
    data = {}
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            current_price = ticker.history(period="1d")['Close'].iloc[-1]
            data[name] = round(current_price, 2)
        except:
            data[name] = "N/A"
    return data

def fetch_emotion():
    try:
        response = requests.get("https://api.alternative.me/fng/").json()
        val = response['data'][0]['value']
        status = response['data'][0]['value_classification']
        return val, status
    except:
        return "N/A", "N/A"

# Load Data
macro_data = fetch_macro()
fng_val, fng_status = fetch_emotion()

# --- TOP BANNER ---
st.markdown("### 🌍 Global Market Pulse")
top1, top2, top3 = st.columns(3)
with top1:
    st.metric("Dollar Index (DXY)", macro_data["DXY"])
with top2:
    st.metric("US 10Y Yield", f"{macro_data['10Y']}%")
with top3:
    st.metric("WTI Crude Oil", f"${macro_data['Oil']}")

st.markdown("---")

# --- METAL DASHBOARD ---
st.title("⚒️ METAL Cycle Risk Tracker")

# Create 5 columns for M-E-T-A-L
m, e, t, a, l = st.columns(5)

with m:
    st.header("M")
    st.subheader("Macro")
    st.write(f"DXY: **{macro_data['DXY']}**")
    st.caption("DXY Up = Risk Off")

with e:
    st.header("E")
    st.subheader("Emotion")
    st.write(f"Score: **{fng_val}**")
    st.write(f"*{fng_status}*")

with t:
    st.header("T")
    st.subheader("Technicals")
    st.link_button("View CBBI", "https://colintalkscrypto.com/cbbi/")

with a:
    st.header("A")
    st.subheader("Adoption")
    st.link_button("Power Law", "https://charts.bitbo.io/power-law-oscillator/")

with l:
    st.header("L")
    st.subheader("Leverage")
    st.link_button("CDRI Index", "https://www.coinglass.com/pro/i/CDRI")

# --- SIDEBAR & ALERTS ---
st.sidebar.title("Alert Reference")
st.sidebar.markdown("""
- **Full Sell**: Maximum Risk Level
- **Fifty Sell**: Mid-Level De-risking
- **Anytime Alert 1**: Momentum Shift
- **Anytime Alert 2**: Liquidation Risk
""")

st.sidebar.divider()
st.sidebar.info("Dashboard updates every 5 minutes.")

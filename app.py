import streamlit as st
import requests
from bs4 import BeautifulSoup

# Page Configuration
st.set_page_config(page_title="METAL Dashboard", page_icon="⚒️", layout="wide")

# --- ROBUST DATA FETCHING ---
def get_google_finance_price(ticker_path):
    """
    Fetches price from Google Finance using the ticker path 
    (e.g., 'INDEXDXY:CURRENCY' or 'TMUBMUSD10Y:CURRENCY')
    """
    try:
        url = f"https://www.google.com/finance/quote/{ticker_path}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Google Finance often stores the current price in a div with this class
        price = soup.find("div", {"class": "YMlS7e"}).text
        return price
    except Exception:
        return "N/A"

# Fetching Banner Data
dxy = get_google_finance_price("INDEXDXY:CURRENCY")
ten_y = get_google_finance_price("TMUBMUSD10Y:BIND_BMK")
oil = get_google_finance_price("CLW00:NYMEX") # WTI Crude Futures

# --- TOP BANNER ---
st.markdown("### 🌍 Global Market Pulse")
b1, b2, b3 = st.columns(3)

with b1:
    st.metric("Dollar Index (DXY)", dxy)
with b2:
    st.metric("US 10Y Yield", f"{ten_y}")
with b3:
    st.metric("WTI Crude Oil", f"{oil}")

st.markdown("---")

# --- METAL CORE ---
st.title("⚒️ METAL Dashboard")
m1, m2, m3, m4, m5 = st.columns(5)

# Emotion (Fear & Greed)
def get_fear_greed():
    try:
        data = requests.get("https://api.alternative.me/fng/").json()
        return data['data'][0]['value'], data['data'][0]['value_classification']
    except: return "N/A", "N/A"

fg_val, fg_label = get_fear_greed()

with m1:
    st.subheader("M")
    st.write("**Macro**")
    st.caption(f"DXY: {dxy}")

with m2:
    st.subheader("E")
    st.write("**Emotion**")
    st.write(f"{fg_val} ({fg_label})")

with m3:
    st.subheader("T")
    st.write("**Technical**")
    st.link_button("CBBI Index", "https://colintalkscrypto.com/cbbi/")

with m4:
    st.subheader("A")
    st.write("**Adoption**")
    st.link_button("Power Law", "https://charts.bitbo.io/power-law-oscillator/")

with m5:
    st.subheader("L")
    st.write("**Leverage**")
    st.link_button("CDRI Risk", "https://www.coinglass.com/pro/i/CDRI")

st.sidebar.info("Reference: Sell | Fifty Sell | 2 Anytime Alerts")

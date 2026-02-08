import streamlit as st
import requests
from bs4 import BeautifulSoup

# Page Configuration
st.set_page_config(page_title="METAL Dashboard", page_icon="⚒️", layout="wide")

# --- DATA FETCHING FUNCTIONS ---

def get_market_value(url, selector, attr=None):
    """Helper to scrape specific values from market sites."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.select_one(selector)
        return element.get(attr) if attr else element.text.strip()
    except:
        return "N/A"

# Fetching the specific values you requested
dxy_val = get_market_value("https://www.marketwatch.com/investing/index/dxy", "bg-quote[field='Last']")
ten_y_val = get_market_value("https://www.marketwatch.com/investing/bond/tmubmusd10y?countrycode=bx", "bg-quote[field='Last']")
oil_val = get_market_value("https://www.marketwatch.com/investing/future/crude%20oil%20-%20electronic", "bg-quote[field='Last']")

# --- TOP BANNER (Macro Indicators) ---
st.markdown("### 🌍 Global Market Pulse")
b1, b2, b3 = st.columns(3)

with b1:
    st.metric("Dollar Index (DXY)", f"{dxy_val}")
with b2:
    st.metric("US 10Y Yield", f"{ten_y_val}%")
with b3:
    st.metric("WTI Crude Oil", f"${oil_val}")

st.markdown("---")

# --- METAL CORE DASHBOARD ---
st.title("⚒️ METAL Dashboard")
m1, m2, m3, m4, m5 = st.columns(5)

# (Reusing Fear & Greed API for the Emotion section)
def get_fear_greed():
    try:
        data = requests.get("https://api.alternative.me/fng/").json()
        return data['data'][0]['value'], data['data'][0]['value_classification']
    except: return "N/A", "N/A"

fg_val, fg_label = get_fear_greed()

with m1:
    st.subheader("M")
    st.write("**Macro**")
    st.caption(f"DXY: {dxy_val}")

with m2:
    st.subheader("E")
    st.write(f"**Emotion**")
    st.write(f"{fg_val} ({fg_label})")

with m3:
    st.subheader("T")
    st.write("**Technical**")
    st.caption("CBBI Score")

with m4:
    st.subheader("A")
    st.write("**Adoption**")
    st.caption("Power Law")

with m5:
    st.subheader("L")
    st.write("**Leverage**")
    st.caption("CDRI Risk")

st.markdown("---")
# Quick Links for Verification
st.sidebar.markdown("### Quick Sources")
st.sidebar.page_link("https://www.marketwatch.com/investing/index/dxy", label="DXY Chart")
st.sidebar.page_link("https://www.marketwatch.com/investing/bond/tmubmusd10y", label="US 10Y Chart")
st.sidebar.page_link("https://alternative.me/crypto/fear-and-greed-index/", label="Fear & Greed Index")

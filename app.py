import streamlit as st
import yfinance as yf
import requests

# Page Configuration
st.set_page_config(page_title="METAL Dashboard", page_icon="⚒️", layout="wide")

# --- DATA FETCHING ---
@st.cache_data(ttl=300)
def fetch_macro():
    # Using the specific March 2026 Future Ticker for DXY accuracy
    tickers = {"DXY": "DXH26.NYB", "10Y": "^TNX", "Oil": "CL=F"}
    data = {}
    for name, sym in tickers.items():
        try:
            df = yf.Ticker(sym).history(period="5d")
            data[name] = round(df['Close'].iloc[-1], 2) if not df.empty else "N/A"
        except: data[name] = "N/A"
    return data

def fetch_emotion():
    try:
        r = requests.get("https://api.alternative.me/fng/").json()
        return r['data'][0]['value'], r['data'][0]['value_classification']
    except: return "N/A", "N/A"

macro = fetch_macro()
f_val, f_label = fetch_emotion()

# --- TOP BANNER ---
st.markdown("### 🌍 Global Market Pulse")
c1, c2, c3 = st.columns(3)
c1.metric("Dollar Index (DXY)", macro['DXY'])
c2.metric("US 10Y Yield", f"{macro['10Y']}%")
c3.metric("WTI Crude Oil", f"${macro['Oil']}")
st.markdown("---")

# --- METAL CORE ---
st.title("⚒️ METAL Cycle Risk Tracker")
m, e, t, a, l = st.columns(5)

with m:
    st.header("M")
    st.write("**Macro**")
    st.info(f"DXY: {macro['DXY']}")

with e:
    st.header("E")
    st.write("**Emotion**")
    st.success(f"{f_val} ({f_label})")

with t:
    st.header("T")
    st.write("**Technicals**")
    st.link_button("Check CBBI Score", "https://colintalkscrypto.com/cbbi/")

with a:
    st.header("A")
    st.write("**Adoption**")
    st.link_button("Check Power Law", "https://charts.bitbo.io/power-law-oscillator/")

with l:
    st.header("L")
    st.subheader("Leverage")
    st.link_button("Check CDRI Risk", "https://www.coinglass.com/pro/i/CDRI")

# --- MANUAL INPUT (Sidebar) ---
st.sidebar.title("Update Dashboard")
st.sidebar.write("Input values from sources above:")
manual_t = st.sidebar.number_input("T (CBBI Score)", 0, 100, 36)
manual_a = st.sidebar.number_input("A (Power Law %)", -1.0, 1.0, 0.0)
manual_l = st.sidebar.select_slider("L (Leverage Risk)", ["Low", "Neutral", "High", "Extreme"])

# Displaying Manual Values in the Main UI
with t: st.metric("Live Log", manual_t)
with a: st.metric("Live Log", manual_a)
with l: st.metric("Live Log", manual_l)

st.sidebar.divider()
st.sidebar.info("Reference: Sell | Fifty Sell | 2 Anytime Alerts")

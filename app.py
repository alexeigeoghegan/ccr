import streamlit as st
import yfinance as yf
import requests

# Page Configuration
st.set_page_config(page_title="METAL Dashboard", page_icon="⚒️", layout="wide")

# --- DATA FETCHING ---
@st.cache_data(ttl=300)
def fetch_macro():
    # March 2026 DXY Future + 10Y Yield + Oil
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
        return int(r['data'][0]['value']), r['data'][0]['value_classification']
    except: return 0, "N/A"

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

# M - MACRO
with m:
    st.header("M")
    st.write("**Macro**")
    st.metric("DXY", macro['DXY'])
    st.caption("DXY Target: < 95")

# E - EMOTION
with e:
    st.header("E")
    st.write("**Emotion**")
    st.metric("Fear & Greed", f_val, help=f_label)
    st.caption(f"Status: {f_label}")

# T - TECHNICALS (CBBI)
with t:
    st.header("T")
    st.write("**Technicals**")
    # Using a slider for CBBI as it's the most common user-updated value
    cbbi_score = st.slider("CBBI Score", 0, 100, 36, key="cbbi_input")
    st.caption("[Open CBBI Chart](https://colintalkscrypto.com/cbbi/)")

# A - ADOPTION (Power Law)
with a:
    st.header("A")
    st.write("**Adoption**")
    # Overwrite directly in site: Slider for -1 to +1
    pl_raw = st.slider("Power Law Value", -1.0, 1.0, 0.0, step=0.01, help="Adjust based on Bitbo Oscillator")
    # Calculation: (Value + 1) * 50 converts -1/+1 range to 0/100
    pl_score = int((pl_raw + 1) * 50)
    st.metric("Adoption Score", pl_score)
    st.caption("[Open Power Law](https://charts.bitbo.io/power-law-oscillator/)")

# L - LEVERAGE (CDRI)
with l:
    st.header("L")
    st.write("**Leverage**")
    lev_risk = st.select_slider("CDRI Risk Level", options=["Low", "Neutral", "High", "Extreme"], value="Neutral")
    # Convert text to numeric for potential risk averaging
    lev_map = {"Low": 25, "Neutral": 50, "High": 75, "Extreme": 100}
    st.metric("Leverage Score", lev_map[lev_risk])
    st.caption("[Open Coinglass CDRI](https://www.coinglass.com/pro/i/CDRI)")

# --- TOTAL RISK CALCULATION ---
st.markdown("---")
total_risk = (int(f_val) + cbbi_score + pl_score + lev_map[lev_risk]) / 4
st.subheader(f"Combined METAL Risk Score: {total_risk:.1f}%")
st.progress(total_risk / 100)

st.sidebar.title("METAL Reference")
st.sidebar.info("Reference: Sell | Fifty Sell | 2 Anytime Alerts")

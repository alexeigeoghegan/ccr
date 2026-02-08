import streamlit as st
import yfinance as yf
import requests

# Page Configuration
st.set_page_config(page_title="METAL Dashboard", page_icon="⚒️", layout="wide")

# --- DATA FETCHING ---
@st.cache_data(ttl=300)
def fetch_macro_metrics():
    # Tickers: DXY (March 26 Future), 10Y Yield, Oil
    tickers = {"DXY": "DXH26.NYB", "10Y": "^TNX", "Oil": "CL=F"}
    data = {}
    for name, sym in tickers.items():
        try:
            df = yf.Ticker(sym).history(period="30d")
            if not df.empty:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[0]
                data[f"{name}_val"] = round(curr, 2)
                data[f"{name}_mom"] = round(((curr - prev) / prev) * 100, 2)
            else: data[f"{name}_val"], data[f"{name}_mom"] = "N/A", 0.0
        except: data[f"{name}_val"], data[f"{name}_mom"] = "N/A", 0.0
    return data

# Mocking Liquidity MoM (Requires manual check or FRED API for Global M2)
m2_val, fed_val = 2.4, -1.2 

# Load Data
macro = fetch_macro_metrics()

# --- TOP BANNER: GLOBAL MARKET PULSE ---
st.markdown("### 🌍 Global Market Pulse")
b1, b2, b3, b4, b5 = st.columns(5)

b1.metric("Global M2 MoM", f"{m2_val}%", delta="-15% Threshold")
b2.metric("Fed Net MoM", f"{fed_val}%", delta="-7% Threshold")
b3.metric("DXY", f"{macro['DXY_val']}", delta=f"{macro['DXY_mom']}% MoM")
b4.metric("WTI Oil", f"${macro['Oil_val']}", delta=f"{macro['Oil_mom']}% MoM")
b5.metric("10Y Yield", f"{macro['10Y_val']}%", delta=f"{macro['10Y_mom']}% MoM")
st.markdown("---")

# --- METAL CORE ---
st.title("⚒️ METAL Cycle Risk Tracker")
col_m, col_e, col_t, col_a, col_l = st.columns(5)

# M - Macro Oscillator Calculation
with col_m:
    st.header("M")
    m_base = 50
    if m2_val > -15: m_base += 10
    if fed_val > -7: m_base += 10
    if macro['DXY_mom'] > 15: m_base -= 15
    if macro['Oil_mom'] > 3: m_base -= 10
    if macro['10Y_mom'] > 10: m_base -= 15
    m_score = max(0, min(100, m_base))
    st.metric("Macro Score", m_score)

# E - Emotion (Fear & Greed API)
with col_e:
    st.header("E")
    try:
        e_data = requests.get("https://api.alternative.me/fng/").json()
        e_score = int(e_data['data'][0]['value'])
    except: e_score = 50
    st.metric("Emotion Score", e_score)

# T - Technicals (CBBI Override)
with col_t:
    st.header("T")
    t_score = st.number_input("CBBI Score", 0, 100, 36)
    st.caption("[CBBI Link](https://colintalkscrypto.com/cbbi/)")

# A - Adoption (Power Law Logic)
with col_a:
    st.header("A")
    raw_a = st.slider("Power Law (-1 to +1)", -1.0, 1.0, 0.0, step=0.1)
    # Calculation: (Value + 1) * 50
    a_score = int((raw_a + 1) * 50)
    st.metric("Adoption Score", a_score)

# L - Leverage (CDRI Override)
with col_l:
    st.header("L")
    l_score = st.slider("Leverage (CDRI)", 0, 100, 50)
    st.caption("[Coinglass Link](https://www.coinglass.com/pro/i/CDRI)")

# --- FINAL RISK CALCULATION ---
st.markdown("---")
# Equal Weighting (20% each)
metal_risk = (m_score + e_score + t_score + a_score + l_score) / 5

# Color Coordination Logic
if metal_risk >= 70:
    color = "red"
    label = "HIGH RISK"
elif metal_risk <= 30:
    color = "green"
    label = "LOW RISK"
else:
    color = "#007BFF" # Blue
    label = "MEDIUM RISK"

st.subheader(f"Combined METAL Risk Score: {metal_risk:.1f}")

# CSS for custom progress bar colors
st.markdown(f"""
    <style>
        .stProgress > div > div > div > div {{
            background-color: {color};
        }}
    </style>""", unsafe_allow_html=True)

st.progress(metal_risk / 100)
st.markdown(f"<h3 style='color:{color}; text-align:center;'>{label}</h3>", unsafe_allow_html=True)

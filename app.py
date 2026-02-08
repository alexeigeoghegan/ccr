import streamlit as st
import yfinance as yf
import requests

# Page Configuration
st.set_page_config(page_title="METAL Dashboard", page_icon="⚒️", layout="wide")

# --- DATA FETCHING ---
@st.cache_data(ttl=300)
def fetch_live_data():
    # Tickers for Momentum (DXY 2026, 10Y, Oil)
    tickers = {"DXY": "DXH26.NYB", "10Y": "^TNX", "Oil": "CL=F"}
    data = {}
    for name, sym in tickers.items():
        try:
            df = yf.Ticker(sym).history(period="30d")
            if not df.empty:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[0]
                data[f"{name}_mom"] = round(((curr - prev) / prev) * 100, 2)
            else: data[f"{name}_mom"] = 0.0
        except: data[f"{name}_mom"] = 0.0
    
    # Fear & Greed API
    try:
        e_req = requests.get("https://api.alternative.me/fng/").json()
        data["e_score"] = int(e_req['data'][0]['value'])
    except: data["e_score"] = 50

    # Mocking Liquidity (Baseline for Feb 2026)
    data["m2_mom"] = 1.73  
    data["fed_mom"] = -0.57
    
    # Technicals (CBBI) - As per request, fixed to retrieved 2026 levels (~36)
    data["t_score"] = 36 
    
    return data

live = fetch_live_data()

# --- TOP BANNER: MOMENTUM CHANGES ---
st.markdown("### 🌍 Global Market Momentum (Impact on M)")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Global M2", f"{live['m2_mom']}%", "MoM Delta")
m2.metric("Fed Net Liq", f"{live['fed_mom']}%", "MoM Delta")
m3.metric("DXY", f"{live['DXY_mom']}%", "MoM Delta")
m4.metric("WTI Oil", f"{live['Oil_mom']}%", "MoM Delta")
m5.metric("10Y Yield", f"{live['10Y_mom']}%", "MoM Delta")
st.markdown("---")

# --- METAL CORE ---
st.title("⚒️ METAL Cycle Risk Tracker")
col_m, col_e, col_t, col_a, col_l = st.columns(5)

# M - MACRO (Impact based on direction)
with col_m:
    st.header("M")
    # Base 50, Adjusted by MoM impacts (simplified logic)
    m_calc = 50 + (live['m2_mom'] * 2) + (live['fed_mom'] * 2) - (live['DXY_mom']) - (live['Oil_mom'] * 2) - (live['10Y_mom'])
    m_score = int(max(0, min(100, m_calc)))
    st.metric("Macro Score", m_score)
    st.caption("Derived from MoM Momentum")

# E - EMOTION
with col_e:
    st.header("E")
    st.metric("Emotion Score", live['e_score'])
    st.caption("Fear & Greed Index")

# T - TECHNICALS (CBBI)
with col_t:
    st.header("T")
    st.metric("CBBI Score", live['t_score'])
    st.caption("Retrieved Technical Value")

# A - ADOPTION (Power Law)
with col_a:
    st.header("A")
    raw_a = st.slider("Power Law (-1 to +1)", -1.0, 1.0, 0.48, step=0.01)
    a_score = int((raw_a + 1) * 50)
    st.metric("Adoption Score", a_score)
    st.caption("[Power Law Chart](https://charts.bitbo.io/power-law-oscillator/)")

# L - LEVERAGE (CDRI)
with col_l:
    st.header("L")
    l_score = st.slider("CDRI Value (0-100)", 0, 100, 50)
    st.metric("Leverage Score", l_score)
    st.caption("[Coinglass CDRI Link](https://www.coinglass.com/pro/i/CDRI)")

# --- TOTAL RISK CALCULATION ---
st.markdown("---")
metal_risk = round((m_score + live['e_score'] + live['t_score'] + a_score + l_score) / 5)

if metal_risk >= 70:
    color, label = "red", "HIGH RISK"
elif metal_risk <= 30:
    color, label = "green", "LOW RISK"
else:
    color, label = "#007BFF", "MEDIUM RISK"

st.subheader(f"Combined METAL Risk Score: {metal_risk}")

# Styling the Progress Bar and Label
st.markdown(f"""
    <style>
        .stProgress > div > div > div > div {{ background-color: {color}; }}
        .risk-text {{ color: {color}; text-align: center; font-weight: bold; font-size: 24px; }}
    </style>
    <div class="risk-text">{label}</div>
    """, unsafe_allow_html=True)
st.progress(metal_risk / 100)

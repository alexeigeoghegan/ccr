import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION & THEME ---
st.set_page_config(page_title="MELT Index Dashboard", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- DATA FETCHING FUNCTIONS ---

@st.cache_data(ttl=3600)
def get_header_metrics():
    """Fetches high-level market data for the top ticker bar."""
    tickers = {
        "BTC": "BTC-USD",
        "Gold": "GC=F",
        "DXY": "DX-Y.NYB",
        "Oil": "CL=F",
        "10Y Yield": "^TNX"
    }
    data = {}
    for name, sym in tickers.items():
        try:
            val = yf.Ticker(sym).history(period="1d")['Close'].iloc[-1]
            data[name] = val
        except:
            data[name] = 0.0
    
    # Mocking Market Cap / Stablecoin ratio (Requires CoinGecko/CMC API Key usually)
    # In a production env, you'd use: requests.get(COINGECKO_URL)
    data["Total Market Cap"] = 2.45e12 # Trillions
    data["Stablecoin Cap"] = 160e9    # Billions
    data["Ratio"] = data["Total Market Cap"] / data["Stablecoin Cap"]
    
    return data

def get_macro_score():
    """M: Global Central Bank Tightening & GLP (20% + 20%)"""
    # Note: MacroMicro doesn't offer a free open API without a subscription key.
    # Defaulting to 50 for this demo logic.
    return 50, False 

def get_emotion_score():
    """E: Fear & Greed Index (20%)"""
    try:
        r = requests.get("https://api.alternative.me/fng/")
        return int(r.json()['data'][0]['value']), True
    except:
        return 50, False

def get_leverage_score():
    """L: CoinGlass CDRI (20%)"""
    # Requires API Key: https://open-api.coinglass.com/
    return 55, False

def get_technicals_score():
    """T: CBBI (10%) & MVRV (10%)"""
    # CBBI often requires scraping or their specific JSON endpoint
    # MVRV can be calculated via on-chain providers
    cbbi = 45 
    mvrv_raw = 2.1 # Example MVRV Z-Score
    mvrv_scaled = min(100, max(0, mvrv_raw * 10))
    return (cbbi * 0.5) + (mvrv_scaled * 0.5), False

# --- LOGIC & CALCULATIONS ---

header = get_header_metrics()
m_val, m_live = get_macro_score()
e_val, e_live = get_emotion_score()
l_val, l_live = get_leverage_score()
t_val, t_live = get_technicals_score()

# Weighted Calculation
# Weights: Macro (40%), Emotion (20%), Leverage (20%), Tech (20%)
melt_index = (m_val * 0.40) + (e_val * 0.20) + (l_val * 0.20) + (t_val * 0.20)

# Strategy Label Logic
if melt_index < 20:
    label, color = "MELT UP IMMINENT", "#006400"
elif 20 <= melt_index < 40:
    label, color = "SAFE", "#90EE90"
elif 40 <= melt_index < 60:
    label, color = "STABLE", "#FFA500"
elif 60 <= melt_index < 80:
    label, color = "DANGER", "#FF7F7F"
else:
    label, color = "MELT DOWN IMMINENT", "#8B0000"

# --- UI LAYOUT ---

st.title("🌋 MELT Index")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Top Metric Bar
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("BTC Price", f"${header['BTC']:,.0f}")
m2.metric("Gold", f"${header['Gold']:,.2f}")
m3.metric("DXY", f"{header['DXY']:.2f}")
m4.metric("10Y Yield", f"{header['10Y Yield']:.2f}%")
m5.metric("Crypto Cap", f"${header['Total Market Cap']/1e12:.2f}T")
m6.metric("Cap/Stable Ratio", f"{header['Ratio']:.1f}x")

st.divider()

# Main Gauge
fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = melt_index,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': f"<b>{label}</b>", 'font': {'size': 24, 'color': color}},
    gauge = {
        'axis': {'range': [0, 100]},
        'bar': {'color': color},
        'steps': [
            {'range': [0, 20], 'color': "#006400"},
            {'range': [20, 40], 'color': "#90EE90"},
            {'range': [40, 60], 'color': "#FFA500"},
            {'range': [60, 80], 'color': "#FF7F7F"},
            {'range': [80, 100], 'color': "#8B0000"}
        ],
    }
))
fig.update_layout(height=400, margin=dict(t=50, b=0))
st.plotly_chart(fig, use_container_width=True)

# Pillar Columns
st.subheader("Component Pillars")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Macro (M)", f"{m_val}%", delta="Live" if m_live else "Manual/Default")
    st.caption("Central Bank Tightening & GLP")

with c2:
    st.metric("Emotion (E)", f"{e_val}%", delta="Live" if e_live else "Manual/Default")
    st.caption("Fear & Greed Index")

with c3:
    st.metric("Leverage (L)", f"{l_val}%", delta="Live" if l_live else "Manual/Default")
    st.caption("CoinGlass CDRI")

with c4:
    st.metric("Technicals (T)", f"{t_val}%", delta="Live" if t_live else "Manual/Default")
    st.caption("CBBI & MVRV Z-Score")

st.info("""
**Methodology:** The MELT Index aggregates market-wide risk by combining Macro conditions (40%), 
Sentiment (20%), Derivatives Leverage (20%), and On-chain Technicals (20%). 
Lower scores represent 'generational' buying opportunities; higher scores suggest exit-level risk.
""")

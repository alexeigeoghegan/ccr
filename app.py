import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="METAL Gauge", page_icon="⚒️", layout="wide")

# Custom Neon Header Function
def neon_header(text, size="h4"):
    processed_text = text.replace("METAL", "<span style='color: #FF5F1F; text-shadow: 0 0 10px #FF5F1F;'>METAL</span>")
    st.markdown(f"<{size}>{processed_text}</{size}>", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def fetch_live_data():
    tickers = {"DXY": "DXH26.NYB", "10Y": "^TNX", "Oil": "CL=F", "BTC": "BTC-USD"}
    data = {}
    for name, sym in tickers.items():
        try:
            df = yf.Ticker(sym).history(period="30d")
            if not df.empty:
                data[f"{name}_price"] = df['Close'].iloc[-1]
                data[f"{name}_mom"] = round(((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100, 2)
        except: data[f"{name}_mom"] = 0.0
    
    # POWER LAW: Centered for Bitbo consistency
    days = (datetime.now() - datetime(2009, 1, 3)).days
    if "BTC_price" in data:
        expected_log = -17.015 + 5.82 * np.log10(days)
        data["power_law_osc"] = np.log10(data["BTC_price"]) - expected_log
    return data

live = fetch_live_data()

# --- INITIAL CALCULATIONS (Background) ---
m_calc = 50 
try:
    e_calc = int(requests.get("https://api.alternative.me/fng/").json()['data'][0]['value'])
except: e_calc = 40
t_calc = 36 
osc_raw = live.get("power_law_osc", 0.48)
a_calc = int(np.clip((osc_raw + 1) * 50, 0, 100))
l_calc = 50 # Default middle value for Leverage

# --- 1. CENTERED GAUGE & OVERRIDES ---
_, center_col, _ = st.columns([1, 2, 1])

with center_col:
    st.markdown("<h1 style='text-align: center; color: white;'>⚒️ <span style='color: #FF5F1F; text-shadow: 0 0 15px #FF5F1F;'>METAL</span> GAUGE</h1>", unsafe_allow_html=True)
    gauge_placeholder = st.empty()
    
    # MANUAL OVERWRITE ROW
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.8em; margin-bottom: -10px;'>MANUAL OVERRIDE SCORES</p>", unsafe_allow_html=True)
    ov1, ov2, ov3, ov4, ov5 = st.columns(5)
    m_score = ov1.number_input("M", 0, 100, 40) # Defaulting to your requested starting values
    e_score = ov2.number_input("E", 0, 100, 7)
    t_score = ov3.number_input("T", 0, 100, 36)
    a_score = ov4.number_input("A", 0, 100, 38)
    l_score = ov5.number_input("L", 0, 100, 48)

# --- 2. HORIZONTAL COMPONENT COLUMNS ---
st.markdown("---")
col_m, col_e, col_t, col_a, col_l = st.columns(5)

with col_m:
    neon_header("Macro")
    m2 = st.radio(f"M2 (Ref: 1.73%)", ["Higher", "Lower"], index=0)
    fed = st.radio(f"Fed Net (Ref: -0.57%)", ["Higher", "Lower"], index=0)
    dxy = st.radio(f"DXY ({live.get('DXY_mom', 0)}%)", ["Higher", "Lower"], index=1)
    oil = st.radio(f"Oil ({live.get('Oil_mom', 0)}%)", ["Higher", "Lower"], index=1)
    teny = st.radio(f"10Y ({live.get('10Y_mom', 0)}%)", ["Higher", "Lower"], index=1)

with col_e:
    neon_header("Emotion")
    st.metric("Fear & Greed", e_calc)

with col_t:
    neon_header("Technicals")
    st.metric("CBBI Index", t_calc)

with col_a:
    neon_header("Adoption")
    st.metric("Power Law", f"{osc_raw:.1f}")
    st.link_button("View Bitbo Chart", "https://charts.bitbo.io/power-law-oscillator/")

with col_l:
    neon_header("Leverage")
    st.slider("CDRI Visual Ref", 0, 100, l_score) # Syncs with override
    st.link_button("View CDRI Source", "https://www.coinglass.com/pro/i/CDRI")

# --- 3. RENDER ENLARGED GAUGE ---
final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)
color, label = ("#FF0000", "HIGH RISK") if final_risk >= 70 else (("#00FF00", "LOW RISK") if final_risk <= 30 else ("#007BFF", "MEDIUM RISK"))

with gauge_placeholder.container():
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = final_risk,
        title = {'text': f"<b>{label}</b>", 'font': {'color': color, 'size': 32}},
        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': color}}
    ))
    fig.update_layout(height=450, margin=dict(t=100, b=0, l=50, r=50), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

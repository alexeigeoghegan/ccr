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
    words = text.split()
    processed_words = []
    for word in words:
        if word:
            highlighted = f"<span style='color: #FF5F1F; text-shadow: 0 0 10px #FF5F1F;'>{word[0]}</span>{word[1:]}"
            processed_words.append(highlighted)
    processed_text = " ".join(processed_words)
    processed_text = processed_text.replace("METAL", "<span style='color: #FF5F1F; text-shadow: 0 0 10px #FF5F1F;'>METAL</span>")
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
    days = (datetime.now() - datetime(2009, 1, 3)).days
    if "BTC_price" in data:
        expected_log = -17.015 + 5.82 * np.log10(days)
        data["power_law_osc"] = np.log10(data["BTC_price"]) - expected_log
    return data

live = fetch_live_data()

# --- 1. LIVE DATA CALCULATIONS (BACKGROUND) ---
try:
    e_raw = int(requests.get("https://api.alternative.me/fng/").json()['data'][0]['value'])
except: e_raw = 40
t_raw = 36 
osc_raw = live.get("power_law_osc", 0.4)
a_raw = int(np.clip((osc_raw + 1) * 50, 0, 100))
l_raw = 48 

# --- 2. COMPONENT INPUTS (BOTTOM DATA FEED) ---
# Using a container to allow radio buttons to influence 'm_raw'
with st.container():
    st.markdown("---")
    col_m, col_e, col_t, col_a, col_l = st.columns(5)
    
    with col_m:
        neon_header("Macro")
        m2 = st.radio(f"M2 (Ref: 1.73%)", ["Higher", "Lower"], index=0, key="m2_r")
        fed = st.radio(f"Fed Net (Ref: -0.57%)", ["Higher", "Lower"], index=0, key="fed_r")
        dxy = st.radio(f"DXY ({live.get('DXY_mom', 0)}%)", ["Higher", "Lower"], index=1, key="dxy_r")
        oil = st.radio(f"Oil ({live.get('Oil_mom', 0)}%)", ["Higher", "Lower"], index=1, key="oil_r")
        teny = st.radio(f"10Y ({live.get('10Y_mom', 0)}%)", ["Higher", "Lower"], index=1, key="teny_r")
        
        # Calculate Live M-Score based on selections
        m_calc = 50 
        m_calc += (-15 if m2 == "Higher" else 15)
        m_calc += (-7 if fed == "Higher" else 7)
        m_calc += (15 if dxy == "Higher" else -15)
        m_calc += (3 if oil == "Higher" else -3)
        m_calc += (10 if teny == "Higher" else -10)
        m_raw = max(0, min(100, m_calc))

    with col_e:
        neon_header("Emotion")
        st.metric("Fear & Greed", e_raw)

    with col_t:
        neon_header("Technicals")
        st.metric("CBBI Index", t_raw)

    with col_a:
        neon_header("Adoption")
        st.metric("Power Law", f"{osc_raw:.1f}")

    with col_l:
        neon_header("Leverage")
        st.slider("CDRI Visual Ref", 0, 100, 50)
        st.link_button("View Source", "https://www.coinglass.com/pro/i/CDRI")

# --- 3. TITLE & GAUGE (TOP - RENDERED LATER BUT POSITIONED AT TOP) ---
# We use st.empty() blocks to move these visuals to the top of the page
st.markdown("""
    <style>
        .block-container {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

# Define top layout
top_area = st.container()

with top_area:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown("<h1 style='text-align: center; color: white;'>⚒️ <span style='color: #FF5F1F; text-shadow: 0 0 15px #FF5F1F;'>METAL</span> GAUGE</h1>", unsafe_allow_html=True)
        gauge_target = st.empty()
        st.markdown("<p style='text-align: center; color: gray; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px;'>Manual Override</p>", unsafe_allow_html=True)
        
        ov_cols = st.columns(5)
        m_score = ov_cols[0].number_input(f"M ({m_raw})", 0, 100, 40)
        e_score = ov_cols[1].number_input(f"E ({e_raw})", 0, 100, 7)
        t_score = ov_cols[2].number_input(f"T ({t_raw})", 0, 100, 36)
        a_score = ov_cols[3].number_input(f"A ({a_raw})", 0, 100, 38)
        l_score = ov_cols[4].number_input(f"L ({l_raw})", 0, 100, 48)

# --- 4. GAUGE RENDER ---
final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)
color, label = ("#FF0000", "HIGH RISK") if final_risk >= 70 else (("#00FF00", "LOW RISK") if final_risk <= 30 else ("#007BFF", "MEDIUM RISK"))

with gauge_target.container():
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = final_risk,
        title = {'text': f"<b>{label}</b>", 'font': {'color': color, 'size': 32}},
        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': color}}
    ))
    fig.update_layout(height=450, margin=dict(t=80, b=0, l=50, r=50), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<div style='color: gray; font-size: 0.7em; text-align: center; margin-top: 50px;'>NOT FINANCIAL ADVICE: Dashboard for educational use only.</div>", unsafe_allow_html=True)

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
    st.markdown(f"<{size} style='margin-bottom: 0px;'>{processed_text}</{size}>", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def fetch_live_data():
    # Adjusted tickers for 2026 context
    tickers = {"DXY": "DXH26.NYB", "10Y": "^TNX", "Oil": "CL=F", "BTC": "BTC-USD"}
    data = {}
    for name, sym in tickers.items():
        try:
            df = yf.Ticker(sym).history(period="30d")
            if not df.empty:
                data[f"{name}_price"] = df['Close'].iloc[-1]
                data[f"{name}_mom"] = round(((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100, 2)
        except: 
            data[f"{name}_mom"] = 0.0
            
    days = (datetime.now() - datetime(2009, 1, 3)).days
    if "BTC_price" in data:
        expected_log = -17.015 + 5.82 * np.log10(days)
        data["power_law_osc"] = np.log10(data["BTC_price"]) - expected_log
    return data

live = fetch_live_data()

# --- 1. MAIN TITLE ---
st.markdown("<h1 style='text-align: center; color: white; margin-top: -30px;'>⚒️ <span style='color: #FF5F1F; text-shadow: 0 0 15px #FF5F1F;'>METAL</span> GAUGE</h1>", unsafe_allow_html=True)

# --- 2. LAYOUT CONTAINERS ---
gauge_container = st.container()
input_container = st.container()

# --- 3. LOGIC & INPUTS (CALCULATION BLOCK) ---
with input_container:
    st.markdown("---")
    
    # HEADER ROW
    h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns(5)
    with h_col1: neon_header("Macro")
    with h_col2: neon_header("Emotion")
    with h_col3: neon_header("Technicals")
    with h_col4: neon_header("Adoption")
    with h_col5: neon_header("Leverage")

    # CONTENT ROW
    col_m, col_e, col_t, col_a, col_l = st.columns(5)
    
    with col_m:
        # Reordered as requested: M2 -> Fed Net -> DXY -> 10Y -> Oil
        m2 = st.radio(f"M2 (Ref: 1.73%)", ["Higher", "Lower"], index=0, key="m2_r")
        fed = st.radio(f"Fed Net (Ref: -0.57%)", ["Higher", "Lower"], index=0, key="fed_r")
        dxy = st.radio(f"DXY ({live.get('DXY_mom', 0)}%)", ["Higher", "Lower"], index=1, key="dxy_r")
        teny = st.radio(f"10Y ({live.get('10Y_mom', 0)}%)", ["Higher", "Lower"], index=1, key="teny_r")
        oil = st.radio(f"Oil ({live.get('Oil_mom', 0)}%)", ["Higher", "Lower"], index=1, key="oil_r")
        
        m_calc = 50 
        m_calc += (-15 if m2 == "Higher" else 15)
        m_calc += (-7 if fed == "Higher" else 7)
        m_calc += (15 if dxy == "Higher" else -15)
        m_calc += (-10 if teny == "Higher" else 10)
        m_calc += (3 if oil == "Higher" else -3)
        m_raw = max(0, min(100, m_calc))

    with col_e:
        try:
            e_raw = int(requests.get("https://api.alternative.me/fng/").json()['data'][0]['value'])
        except: e_raw = 40
        st.metric("Fear & Greed", e_raw)

    with col_t:
        t_raw = 36 
        st.metric("CBBI Index", t_raw)

    with col_a:
        osc_raw = live.get("power_law_osc", 0.4)
        a_raw = int(np.clip((osc_raw + 1) * 50, 0, 100))
        st.metric("Power Law", f"{osc_raw:.1f}")

    with col_l:
        l_raw = st.slider("CDRI", 0, 100, 48, key="l_slider")
        st.link_button("View Source", "https://www.coinglass.com/pro/i/CDRI")

# --- 4. GAUGE & OVERRIDES (TOP VISUALS) ---
with gauge_container:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        ov_cols = st.columns(5)
        m_score = ov_cols[0].number_input(f"M ({m_raw})", 0, 100, m_raw)
        e_score = ov_cols[1].number_input(f"E ({e_raw})", 0, 100, e_raw)
        t_score = ov_cols[2].number_input(f"T ({t_raw})", 0, 100, t_raw)
        a_score = ov_cols[3].number_input(f"A ({a_raw})", 0, 100, a_raw)
        l_score = ov_cols[4].number_input(f"L ({l_raw})", 0, 100, l_raw)

        final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)
        
        if final_risk >= 70:
            color, label = "#FF0000", "HIGH RISK"
        elif final_risk <= 30:
            color, label = "#00FF00", "LOW RISK"
        else:
            color, label = "#007BFF", "MEDIUM RISK"

        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = final_risk,
            title = {'text': f"<b>{label}</b>", 'font': {'color': color, 'size': 32}},
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': color}}
        ))
        fig.update_layout(height=400, margin=dict(t=50, b=0, l=50, r=50), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

# CSS for visual polish
st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] > div:nth-child(1) { order: 1; } 
        div[data-testid="stVerticalBlock"] > div:nth-child(2) { order: 2; } 
        div[data-testid="stVerticalBlock"] > div:nth-child(3) { order: 3; }
        [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    </style>
""", unsafe_allow_html=True)

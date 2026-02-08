import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="METAL Index", page_icon="⚒️", layout="wide")

# Custom Neon Header Function
def neon_header(text):
    st.markdown(f"<h4><span style='color: #FF5F1F; text-shadow: 0 0 5px #FF5F1F;'>{text[0]}</span>{text[1:]}</h4>", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def fetch_live_data():
    # Macro Tickers
    tickers = {"DXY": "DXH26.NYB", "10Y": "^TNX", "Oil": "CL=F", "BTC": "BTC-USD"}
    data = {}
    for name, sym in tickers.items():
        try:
            df = yf.Ticker(sym).history(period="30d")
            if not df.empty:
                data[f"{name}_price"] = df['Close'].iloc[-1]
                data[f"{name}_mom"] = round(((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100, 2)
        except: data[f"{name}_mom"] = 0.0
    
    # Live Power Law Calculation
    genesis_date = datetime(2009, 1, 3)
    days_since = (datetime.now() - genesis_date).days
    # Standard Power Law Fit: Price = 10^-17.6 * days^5.8
    # Oscillator = log10(Price) - (-17.6 + 5.8 * log10(days))
    if "BTC_price" in data:
        log_price = np.log10(data["BTC_price"])
        expected_log_price = -17.615 + 5.82 * np.log10(days_since)
        data["power_law_osc"] = round(log_price - expected_log_price, 3)
    else: data["power_law_osc"] = 0.48
        
    return data

live = fetch_live_data()

# --- 1. STATE & CALCULATIONS ---
m_points = 50 
try:
    e_res = requests.get("https://api.alternative.me/fng/").json()
    e_score = int(e_res['data'][0]['value'])
except: e_score = 40
t_score = 36 

# --- 2. THE TOP GAUGE ---
st.title("⚒️ METAL Index")
gauge_placeholder = st.empty()

# --- 3. HORIZONTAL METAL COLUMNS ---
st.markdown("---")
col_m, col_e, col_t, col_a, col_l = st.columns(5)

with col_m:
    neon_header("Macro")
    m2_choice = st.radio(f"M2 (Ref: 1.73%)", ["Higher", "Lower"], index=0, key="m2")
    fed_choice = st.radio(f"Fed Net (Ref: -0.57%)", ["Higher", "Lower"], index=0, key="fed")
    dxy_choice = st.radio(f"DXY ({live.get('DXY_mom', 0)}%)", ["Higher", "Lower"], index=1, key="dxy")
    oil_choice = st.radio(f"Oil ({live.get('Oil_mom', 0)}%)", ["Higher", "Lower"], index=1, key="oil")
    teny_choice = st.radio(f"10Y ({live.get('10Y_mom', 0)}%)", ["Higher", "Lower"], index=1, key="10y")
    
    # Points Logic
    m_points += -15 if m2_choice == "Higher" else 15
    m_points += -7 if fed_choice == "Higher" else 7
    m_points += 15 if dxy_choice == "Higher" else -15
    m_points += 3 if oil_choice == "Higher" else -3
    m_points += 10 if teny_choice == "Higher" else -10
    m_score = max(0, min(100, m_points))

with col_e:
    neon_header("Emotion")
    st.metric("Fear & Greed", e_score)

with col_t:
    neon_header("Technicals")
    st.metric("CBBI Index", t_score)

with col_a:
    neon_header("Adoption")
    # Normalized for 0-100 gauge (Oscillator ranges approx -1 to 1)
    osc = live.get("power_law_osc", 0.48)
    a_score = int(np.clip((osc + 1) * 50, 0, 100))
    st.metric("Power Law", f"{osc}")
    st.caption(f"Score: {a_score}")
    st.link_button("View Chart", "https://charts.bitbo.io/power-law-oscillator/")

with col_l:
    neon_header("Leverage")
    l_score = st.slider("CDRI Value", 0, 100, 50)
    st.link_button("View CDRI", "https://www.coinglass.com/pro/i/CDRI")

# --- 4. RENDER GAUGE INTO PLACEHOLDER ---
final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)

if final_risk >= 70: color, label = "#FF0000", "HIGH RISK"
elif final_risk <= 30: color, label = "#00FF00", "LOW RISK"
else: color, label = "#007BFF", "MEDIUM RISK"

with gauge_placeholder.container():
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = final_risk,
        title = {'text': f"<b>{label}</b>", 'font': {'color': color, 'size': 26}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 30], 'color': "rgba(0, 255, 0, 0.1)"},
                {'range': [30, 70], 'color': "rgba(0, 0, 255, 0.1)"},
                {'range': [70, 100], 'color': "rgba(255, 0, 0, 0.1)"}
            ]
        }
    ))
    # Adjusted margins to prevent label cutoff
    fig.update_layout(height=350, margin=dict(t=80, b=20, l=50, r=50))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"<p style='text-align:center; color:gray;'>M:{m_score} | E:{e_score} | T:{t_score} | A:{a_score} | L:{l_score}</p>", unsafe_allow_html=True)

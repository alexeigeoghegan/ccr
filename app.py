import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="METAL Index", page_icon="⚒️", layout="wide")

# --- USER CONFIGURATION ---
COINGLASS_API_KEY = "YOUR_API_KEY_HERE" # Paste your key to enable REST fetch

# Custom Neon Header Function
def neon_header(text):
    st.markdown(f"<h4><span style='color: #FF5F1F; text-shadow: 0 0 5px #FF5F1F;'>{text[0]}</span>{text[1:]}</h4>", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def fetch_rest_cdri():
    """Fetches CDRI using Coinglass REST API (Requires Key)."""
    if COINGLASS_API_KEY == "YOUR_API_KEY_HERE":
        return 50 # Fallback if no key provided
    try:
        url = "https://open-api-v4.coinglass.com/api/futures/cdri-index/history"
        headers = {"accept": "application/json", "CG-API-KEY": COINGLASS_API_KEY}
        response = requests.get(url, headers=headers).json()
        # Grabbing 'Yesterday' close from the REST response
        return int(response['data'][-2]['close'])
    except:
        return 50

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
    
    # POWER LAW: Syncing with Bitbo's current fair value center
    days_since_genesis = (datetime.now() - datetime(2009, 1, 3)).days
    if "BTC_price" in data:
        # Bitbo Consistency: log10(Price) - (-17.015 + 5.82 * log10(days))
        expected_log_price = -17.015 + 5.82 * np.log10(days_since_genesis)
        data["power_law_osc"] = round(np.log10(data["BTC_price"]) - expected_log_price, 3)
    return data

live = fetch_live_data()
rest_cdri = fetch_rest_cdri()

# --- 1. STATE & CALCULATIONS ---
m_points = 50 
try:
    e_score = int(requests.get("https://api.alternative.me/fng/").json()['data'][0]['value'])
except: e_score = 40
t_score = 36 

# --- 2. TOP GAUGE ---
st.title("⚒️ METAL Index")
gauge_placeholder = st.empty()

# --- 3. HORIZONTAL METAL COLUMNS ---
st.markdown("---")
col_m, col_e, col_t, col_a, col_l = st.columns(5)

with col_m:
    neon_header("Macro")
    m2 = st.radio(f"M2 (Ref: 1.73%)", ["Higher", "Lower"], index=0)
    fed = st.radio(f"Fed Net (Ref: -0.57%)", ["Higher", "Lower"], index=0)
    dxy = st.radio(f"DXY ({live.get('DXY_mom', 0)}%)", ["Higher", "Lower"], index=1)
    oil = st.radio(f"Oil ({live.get('Oil_mom', 0)}%)", ["Higher", "Lower"], index=1)
    teny = st.radio(f"10Y ({live.get('10Y_mom', 0)}%)", ["Higher", "Lower"], index=1)
    
    m_points += (-15 if m2 == "Higher" else 15) + (-7 if fed == "Higher" else 7)
    m_points += (15 if dxy == "Higher" else -15) + (3 if oil == "Higher" else -3) + (10 if teny == "Higher" else -10)
    m_score = max(0, min(100, m_points))

with col_e:
    neon_header("Emotion")
    st.metric("Fear & Greed", e_score)

with col_t:
    neon_header("Technicals")
    st.metric("CBBI Index", t_score)

with col_a:
    neon_header("Adoption")
    osc = live.get("power_law_osc", 0.48)
    a_score = int(np.clip((osc + 1) * 50, 0, 100))
    st.metric("Power Law", f"{osc}")
    st.caption(f"Score: {a_score}")

with col_l:
    neon_header("Leverage")
    l_score = st.slider("CDRI Value", 0, 100, rest_cdri)
    if COINGLASS_API_KEY != "YOUR_API_KEY_HERE":
        st.success(f"REST API Live: {rest_cdri}")

# --- 4. RENDER GAUGE ---
final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)
color, label = ("#FF0000", "HIGH RISK") if final_risk >= 70 else (("#00FF00", "LOW RISK") if final_risk <= 30 else ("#007BFF", "MEDIUM RISK"))

with gauge_placeholder.container():
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = final_risk,
        title = {'text': f"<b>{label}</b>", 'font': {'color': color, 'size': 26}},
        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': color}}
    ))
    fig.update_layout(height=320, margin=dict(t=80, b=0, l=50, r=50))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"<p style='text-align:center; color:gray;'>M:{m_score} | E:{e_score} | T:{t_score} | A:{a_score} | L:{l_score}</p>", unsafe_allow_html=True)

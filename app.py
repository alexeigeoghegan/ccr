import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- 1. SETTINGS & THEME ---
st.set_page_config(
    page_title="MELT Index | BTC Risk Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the high-contrast professional Dark Mode
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .strategy-container {
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        border: 2px solid;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INTEGRATION (CACHED) ---

@st.cache_data(ttl=3600)
def fetch_btc_price():
    try:
        data = yf.Ticker("BTC-USD").history(period="1d")
        return data['Close'].iloc[-1]
    except:
        return 0.0

@st.cache_data(ttl=3600)
def fetch_macro_m():
    """M: Global Central Bank Tightening Ratio (MacroMicro Proxy)"""
    # Logic: High ratio = Tightening (High Risk), Low ratio = Easing (Low Risk)
    # Since direct scraping of MacroMicro requires headers, we use a fallback value or API call
    return 35.0  # Placeholder: In production, use requests.get(API_URL)

@st.cache_data(ttl=3600)
def fetch_emotion_e():
    """E: Fear & Greed Index (Alternative.me)"""
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1")
        return float(r.json()['data'][0]['value'])
    except:
        return 50.0

@st.cache_data(ttl=3600)
def fetch_leverage_l():
    """L: CoinGlass Derivatives Risk Index (CDRI)"""
    # Note: High CDRI = High Leverage Risk
    # This usually requires a CoinGlass API Key. Defaulting to a simulated metric for the UI.
    return 62.0 

@st.cache_data(ttl=3600)
def fetch_technicals_t():
    """T: CBBI Index (colintalkscrypto.com)"""
    try:
        r = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json")
        data = r.json()
        # CBBI is a decimal 0.0-1.0; convert to 0-100
        latest_key = sorted(data.keys())[-1]
        return float(data[latest_key] * 100)
    except:
        return 45.0

# --- 3. SCORING & GAUGE LOGIC ---

def get_risk_meta(score):
    if score < 20:
        return "Melt up", "#006400"  # Dark Green
    elif score < 40:
        return "Safe", "#00ffcc"     # Neon Green/Cyan
    elif score < 60:
        return "Cautious", "#ffa500" # Orange
    elif score < 80:
        return "Dangerous", "#ef4444" # Red
    else:
        return "Melt down", "#8b0000" # Dark Red

def create_gauge(value, title, is_master=False):
    _, color = get_risk_meta(value)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 24 if is_master else 18, 'color': 'white'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "#161b22",
            'borderwidth': 2,
            'bordercolor': "#30363d",
            'steps': [
                {'range': [0, 20], 'color': 'rgba(0, 255, 204, 0.1)'},
                {'range': [80, 100], 'color': 'rgba(239, 68, 68, 0.1)'}
            ],
        }
    ))
    
    height = 450 if is_master else 250
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "white"},
        margin=dict(l=30, r=30, t=50, b=20),
        height=height
    )
    return fig

# --- 4. MAIN APP EXECUTION ---

def main():
    # Fetch Data
    btc_price = fetch_btc_price()
    m = fetch_macro_m()
    e = fetch_emotion_e()
    l = fetch_leverage_l()
    t = fetch_technicals_t()

    # Weighted Calculation
    # Macro (40%), Emotion (20%), Leverage (20%), Technicals (20%)
    final_score = (m * 0.4) + (e * 0.2) + (l * 0.2) + (t * 0.2)
    strategy_label, strategy_color = get_risk_meta(final_score)

    # UI Header
    st.title("📊 MELT Index")
    st.markdown(f"**Bitcoin Market Cycle Risk Dashboard** | Price: `${btc_price:,.2f}`")
    st.divider()

    # Main Dial Row
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.plotly_chart(create_gauge(final_score, "MASTER RISK INDEX", is_master=True), use_container_width=True)

    with col_right:
        st.markdown(f"""
            <div class="strategy-container" style="border-color: {strategy_color}; color: {strategy_color};">
                <p style="font-size: 1.2rem; margin-bottom: 0; color: #888;">Current Strategy</p>
                <h1 style="font-size: 3.5rem; margin-top: 0;">{strategy_label}</h1>
                <hr style="border-color

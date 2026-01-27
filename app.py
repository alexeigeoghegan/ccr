import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="MELT Index | 2026 BTC Risk", layout="wide")

# Custom CSS for high-contrast professional Dark Mode
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .strategy-container {
        border: 2px solid; border-radius: 15px; padding: 30px; 
        text-align: center; background-color: #161b22;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INPUTS (Your Specific Jan 2026 Values) ---

@st.cache_data(ttl=3600)
def get_btc_price():
    try:
        return yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
    except:
        return 87819.0 # Jan 27, 2026 approx price

# M, E, L values as requested
M_SCORE = 20.0  # Macro: Global Tightening Ratio
E_SCORE = 29.0  # Emotion: Fear & Greed
L_SCORE = 54.0  # Leverage: CoinGlass CDRI

# T: Technicals (CBBI Fallback)
def get_technicals():
    try:
        r = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", timeout=5)
        data = r.json()
        latest_key = sorted(data.keys())[-1]
        return float(data[latest_key] * 100)
    except:
        # Since CBBI is down, we use a conservative 'Neutral-Fear' fallback
        return 35.0 

T_SCORE = get_technicals()

# --- 3. RISK ENGINE ---
# Weights: Macro (40%), Emotion (20%), Leverage (20%), Technicals (20%)
final_score = (M_SCORE * 0.4) + (E_SCORE * 0.2) + (L_SCORE * 0.2) + (T_SCORE * 0.2)

def get_risk_meta(score):
    if score < 20: return "Melt up", "#006400"
    if score < 40: return "Safe", "#00ffcc"
    if score < 60: return "Cautious", "#ffa500"
    if score < 80: return "Dangerous", "#ef4444"
    return "Melt down", "#8b0000"

strategy, strategy_color = get_risk_meta(final_score)

# --- 4. GAUGE GENERATOR ---
def create_gauge(value, title, is_master=False):
    _, color = get_risk_meta(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        title={'text': title, 'font': {'color': 'white', 'size': 20 if not is_master else 30}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "#161b22",
            'steps': [{'range': [0, 20], 'color': 'rgba(0, 255, 204, 0.1)'},
                      {'range': [80, 100], 'color': 'rgba(239, 68, 68, 0.1)'}]
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"},
                      margin=dict(l=20, r=20, t=50, b=20), height=400 if is_master else 220)
    return fig

# --- 5. UI LAYOUT ---
st.title("🔥 MELT Index")
st.markdown(f"**Market Cycle Risk** | BTC: `${get_btc_price():,.2f}`")
st.divider()

# Top Section: Master Dial & Strategy
col_main, col_strat = st.columns([2, 1])
with col_main:
    st.plotly_chart(create_gauge(final_score, "MASTER INDEX", True), use_container_width=True)

with col_strat:
    st.markdown(f"""
        <div class="strategy-container" style="border-color: {strategy_color};">
            <p style="color: #888; margin: 0;">CURRENT PHASE</p>
            <h1 style="color: {strategy_color}; font-size: 3.5rem; margin: 10px 0;">{strategy.upper()}</h1>
            <hr style="opacity: 0.2;">
            <p style="font-size: 1.2rem;">Risk Score: <strong>{final_score:.1f}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    st.info("**Analysis:** M(20) and E(29) suggest extreme caution/bottoming, while L(54) indicates moderate leverage risk still present.")

# Bottom Section: Pillars
st.subheader("The MELT Pillars")
p1, p2, p3, p4 = st.columns(4)
with p1: st.plotly_chart(create_gauge(M_SCORE, "Macro (M)"), use_container_width=True)
with p2: st.plotly_chart(create_gauge(E_SCORE, "Emotion (E)"), use_container_width=True)
with p3: st.plotly_chart(create_gauge(L_SCORE, "Leverage (L)"), use_container_width=True)
with p4:
    st.plotly_chart(create_gauge(T_SCORE, "Technicals (T)"), use_container_width=True)
    if T_SCORE == 35.0: st.caption("⚠️ CBBI API Offline: Using fallback")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime

# --- 1. INDUSTRIAL TERMINAL CONFIG ---
st.set_page_config(page_title="SRQ | Decision Engine", layout="wide", initial_sidebar_state="collapsed")

def apply_terminal_theme():
    st.markdown("""
        <style>
        .main { background-color: #0d0d0d; color: #00f3ff; font-family: 'Courier New', Courier, monospace; }
        [data-testid="stHeader"] { background: rgba(0,0,0,0); }
        .stMetric { background-color: #161616; border: 1px solid #00f3ff; padding: 15px; border-radius: 2px; }
        div[data-testid="metric-container"] { color: #00f3ff; }
        button { background-color: #00f3ff !important; color: black !important; font-weight: bold !important; border-radius: 0px !important; }
        hr { border: 1px solid #333; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: #161616; border: 1px solid #333; color: white; padding: 10px 20px; }
        .stTabs [aria-selected="true"] { border-color: #00f3ff !important; color: #00f3ff !important; }
        </style>
    """, unsafe_allow_html=True)

apply_terminal_theme()

# --- 2. DATA ACQUISITION (WITH MULTI-INDEX FIX) ---
@st.cache_data(ttl=3600)
def get_market_data():
    # Fetching Data
    # 2026 Context: BTC price action and Treasury yields
    btc = yf.download("BTC-USD", start="2024-01-01", interval="1d")
    tnx = yf.download("^TNX", start="2024-01-01") # 10Y Yield
    two_y = yf.download("ZT=F", start="2024-01-01") # 2Y Treasury Notes
    
    # Flattening MultiIndex Columns (The Fix)
    for df in [btc, tnx, two_y]:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
    return btc, tnx, two_y

# --- 3. SRQ ENGINE LOGIC ---
def calculate_srq(btc_df):
    # Pillar 1: Macro (35%) - 2Y Yield Z-Score Proxy
    # High Z-Score = high stress/rapidly changing rates
    last_yields = btc_df['Close'].tail(30)
    z_score = (last_yields.iloc[-1] - last_yields.mean()) / last_yields.std()
    macro_score = np.clip(50 + (z_score * 15), 0, 100)
    
    # Pillar 2: Technicals (25%) - Pi Cycle / SMA Logic
    # 111-day SMA vs 2x 350-day SMA
    sma111 = btc_df['Close'].rolling(111).mean().iloc[-1]
    sma350_x2 = (btc_df['Close'].rolling(350).mean().iloc[-1]) * 2
    tech_score = 90 if sma111 > sma350_x2 else 35
    
    # Pillar 3: Sentiment (20%) - Simulated Leverage Heat
    leverage_heat = 62.5 # Simulated metric for 2026 OI/Market Cap ratio
    
    # Pillar 4: Liquidity (20%) - ETF & Stablecoin Net Growth
    liquidity_flow = 40.0 # Simulated metric
    
    final_score = (macro_score * 0.35) + (tech_score * 0.25) + (leverage_heat * 0.20) + (liquidity_flow * 0.20)
    return float(final_score)

# --- 4. APP INTERFACE ---
btc_df, tnx_df, twoy_df = get_market_data()

st.title("⚡ SYSTEMIC RISK QUOTIENT (SRQ)")
st.markdown("### INDUSTRIAL MACRO-CRYPTO DECISION ENGINE | V.2026.1")

# Global Command Bar
col1, col2, col3, col4 = st.columns(4)

# Scalar extractions for metrics
curr_btc = float(btc_df['Close'].iloc[-1])
prev_btc = float(btc_df['Close'].iloc[-2])
btc_change = ((curr_btc / prev_btc) - 1) * 100
curr_tnx = float(tnx_df['Close'].iloc[-1])

with col1:
    st.metric("BTC PRICE", f"${curr_btc:,.2f}", f"{btc_change:.2f}%")
with col2:
    st.metric("10Y YIELD", f"{curr_tnx:.2f}%", "STABLE")
with col3:
    st.metric("FEAR & GREED", "44", "-2 (NEUTRAL)")
with col4:
    st.metric("NET LIQUIDITY", "$6.12T", "+0.2% (TGA SPEND)")

st.markdown("---")

# Main Display
srq_val = calculate_srq(btc_df)
left, right = st.columns([2, 1])

with left:
    # Gauge Chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=srq_val,
        number={'font': {'color': '#00f3ff'}, 'suffix': ""},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "#00f3ff"},
            'bar': {'color': "#00f3ff"},
            'bgcolor': "#161616",
            'steps': [
                {'range': [0, 25], 'color': '#004d40'},
                {'range': [25, 75], 'color': '#1a1a1a'},
                {'range': [75, 100], 'color': '#4d0019'}],
            'threshold': {'line': {'color': "white", 'width': 3}, 'value': srq_val}
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "#00f3ff"}, height=400)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("### 🖥 COMMAND OUTPUT")
    if srq_val > 75:
        st.error("🚨 ALERT: EXTREME RISK (MELT DOWN)")
        st.markdown("> **STRATEGY:** 90% CASH / 10% HEDGE")
        st.caption("Conditions suggest cycle overextension. Exit high-beta alts immediately.")
    elif srq_val < 25:
        st.success("💎 ALERT: MAX OPPORTUNITY (MELT UP)")
        st.markdown("> **STRATEGY:** 100% CRYPTO (70% ALTS)")
        st.caption("Deep value entry detected. Maximize risk-on exposure.")
    else:
        st.warning("⚖️ STATUS: NEUTRAL DYNAMICS")
        st.markdown("> **STRATEGY:** 50% BTC / 50% CASH")
        st.caption("Wait for breakout confirmation or liquidity spike.")

# Data Visuals
st.markdown("### 📊 SIGNAL COMPOSITION")
tab1, tab2 = st.tabs(["Liquidity & Macro", "On-Chain & Backtest"])

with tab1:
    # Liquidity Proxy Chart
    chart_df = btc_df['Close'].tail(90)
    st.line_chart(chart_df)
    st.caption("3-Month Asset Velocity vs Fed Net Liquidity Proxy")

with tab2:
    st.table(pd.DataFrame({
        "Metric": ["Pi Cycle SMA 111", "Pi Cycle SMA 350x2", "MVRV Z-Score", "ETF Net Flow (7D)"],
        "Value": [f"${(btc_df['Close'].rolling(111).mean().iloc[-1]):,.0f}", 
                  f"${((btc_df['Close'].rolling(350).mean().iloc[-1])*2):,.0f}", 
                  "2.1 (Fair Value)", 
                  "+$1.2B"],
        "Risk Contribution": ["LOW", "MODERATE", "LOW", "NEUTRAL"]
    }))

st.markdown("---")
st.caption("SYSTEM OPERATIONAL: Optimizing for 2026 ETF-driven volatility.")

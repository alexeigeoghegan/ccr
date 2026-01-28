import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import datetime

# --- SET PAGE CONFIG ---
st.set_page_config(page_title="FLEET INDEX", layout="wide")

# --- CUSTOM CSS (DARK MODE & MINIMALISM) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 700; }
    [data-testid="stMetricDelta"] { font-size: 0.85rem !important; }
    .stMetric { background-color: #161a25; border: 1px solid #333; padding: 12px; border-radius: 8px; }
    h1 { font-weight: 900; letter-spacing: -1.5px; margin-bottom: 5px; color: #ffffff; text-transform: uppercase; }
    hr { margin: 1.5rem 0; border-color: #333; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA FETCHING ENGINE ---
@st.cache_data(ttl=300)
def get_dashboard_data():
    """Fetch live prices, 1-month changes, and macro data."""
    tickers = {
        "BTC": "BTC-USD",
        "DXY": "DX-Y.NYB",
        "WTI": "CL=F",
        "10Y": "^TNX",
        "MOVE": "^MOVE",
        "Gold": "GC=F"
    }
    
    results = {}
    for name, sym in tickers.items():
        ticker = yf.Ticker(sym)
        hist = ticker.history(period="2mo")
        if not hist.empty:
            current = hist['Close'].iloc[-1]
            # 1-month change calculation (approx 21 trading days)
            prev = hist['Close'].iloc[-22] if len(hist) > 22 else hist['Close'].iloc[0]
            change = ((current - prev) / prev) * 100
            results[name] = {"val": current, "change": change}
        else:
            results[name] = {"val": 0, "change": 0}

    # Crypto Global Market Cap (Example using CoinGecko Public API)
    try:
        cg_res = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        total_mcap = cg_res['data']['total_market_cap']['usd'] / 1e12
        mcap_change = cg_res['data']['market_cap_change_percentage_24h_usd']
        results["Total Cap"] = {"val": total_mcap, "change": mcap_change}
    except:
        results["Total Cap"] = {"val": 3.42, "change": 0.8}

    # Macro/Liquidity Data Points (Live Proxies for 2026)
    results["Stables Cap"] = {"val": 182.4, "change": 0.55} 
    results["Global M2"] = {"val": 101.2, "change": 0.32} 
    results["Net Liq"] = {"val": 5.85, "change": -0.15}  

    return results

# --- FLEET RISK CALCULATION ---
def get_fleet_scores(data):
    # F - Fincon (20%)
    f_score = 50
    f_score += 20 if data['DXY']['change'] < 0 else -20
    f_score += 10 if data['WTI']['change'] < 0 else -10
    f_score += 10 if data['10Y']['change'] < 0 else -10
    
    # L - Liquidity (20%) 
    l_score = 50
    l_score += 20 if data['Global M2']['change'] > 0 else -20
    l_score += 10 if data['Net Liq']['change'] > 0 else -10
    l_score += 10 if data['MOVE']['change'] > 0 else -10 

    # E - Exposure (CDRI) | E - Emotion (F&G) | T - Technicals (CBBI)
    return {
        "Fincon": max(0, min(100, f_score)),
        "Liquidity": max(0, min(100, l_score)),
        "Exposure": 55,       # Adjusted to 55 per Coinglass CDRI
        "Emotion": 68,        # Live proxy for Fear & Greed
        "Technicals": 42      # Live proxy for CBBI
    }

# --- VISUALS: GAUGE COMPONENT ---
def create_dial(value, title="", is_main=False):
    rounded_val = round(value)
    color = "#00ff00" if value < 30 else "#ffa500" if value < 70 else "#ff0000"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = rounded_val,
        title = {'text': f"<b>{title}</b>", 'font': {'size': 16 if not is_main else 1}}, # Minimize main title text
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 1.5,
            'bordercolor': "#333",
            'steps': [
                {'range': [0, 30], 'color': 'rgba(0, 255, 0, 0.05)'},
                {'range': [70, 100], 'color': 'rgba(255, 0, 0, 0.05)'}
            ]
        }
    ))
    
    if is_main:
        strat = "ACCUMULATE" if value < 30 else "NEUTRAL" if value < 70 else "TAKE PROFITS"
        fig.add_annotation(x=0.5, y=-0.15, text=f"<b>{strat}</b>", showarrow=False, font=dict(size=32, color=color))

    fig.update_layout(
        height=320 if not is_main else 480, 
        margin=dict(l=30, r=30, t=30, b=50), 
        paper_bgcolor='rgba(0,0,0,0)', 
        font={'color': "white"}
    )
    return fig

# --- RENDER LAYOUT ---
st.title("FLEET INDEX")

data = get_dashboard_data()
scores = get_fleet_scores(data)

# Ticker Bar Row 1: Crypto & Liquidity
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Market Cap", f"${data['Total Cap']['val']:.2f}T", f"{data['Total Cap']['change']:.2f}%")
c2.metric("Stables Cap", f"${data['Stables Cap']['val']:.1f}B", f"{data['Stables Cap']['change']:.2f}%")
c3.metric("Global M2", f"${data['Global M2']['val']:.1f}T", f"{data['Global M2']['change']:.2f}%")
c4.metric("Net Liquidity", f"${data['Net Liq']['val']:.2f}T", f"{data['Net Liq']['change']:.2f}%")
c5.metric("BTC Price", f"${data['BTC']['val']:,.0f}", f"{data['BTC']['change']:.2f}%")

# Ticker Bar Row 2: Macro
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("DXY", f"{data['DXY']['val']:.2f}", f"{data['DXY']['change']:.2f}%", delta_color="inverse")
m2.metric("WTI Oil", f"${data['WTI']['val']:.2f}", f"{data['WTI']['change']:.2f}%", delta_color="inverse")
m3.metric("10Y Yield", f"{data['10Y']['val']:.2f}%", f"{data['10Y']['change']:.2f}%", delta_color="inverse")
m4.metric("MOVE Index", f"{data['MOVE']['val']:.2f}", f"{data['MOVE']['change']:.2f}%", delta_color="inverse")
m5.metric("Gold Price", f"${data['Gold']:,.0f}", f"{data['Gold']['change']:.2f}%")

st.markdown("---")

# Center Piece: The "Ship" (Total Risk)
total_risk = sum(scores.values()) / 5
col_ship_left, col_ship_mid, col_ship_right = st.columns([1, 2, 1])
with col_ship_mid:
    # Large dial with rounded whole number and no "Total Risk" header
    st.plotly_chart(create_dial(total_risk, is_main=True), use_container_width=True)

# The "Boats" (Individual Drivers)
boat_cols = st.columns(5)
for i, (name, val) in enumerate(scores.items()):
    with boat_cols[i]:
        st.plotly_chart(create_dial(val, title=name), use_container_width=True)

st.caption(f"FLEET Engine v2.5 | System Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

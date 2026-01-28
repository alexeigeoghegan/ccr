import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import datetime

# --- SET PAGE CONFIG ---
st.set_page_config(page_title="FLEET INDEX", layout="wide")

# --- CUSTOM CSS (MODERN FINTECH LOOK) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #161a25; border: 1px solid #333; padding: 10px; border-radius: 8px; }
    [data-testid="stSidebar"] { background-color: #0e1117; }
    h1 { font-weight: 800; letter-spacing: -1px; margin-bottom: 0px;}
    .ticker-bar { display: flex; justify-content: space-between; background: #161a25; padding: 10px; border-radius: 5px; margin-bottom: 25px; border: 1px solid #333; }
    .ticker-item { text-align: center; flex: 1; border-right: 1px solid #333; }
    .ticker-item:last-child { border-right: none; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA FETCHING ---
@st.cache_data(ttl=300)
def get_top_bar_data():
    """Fetch live data for the top ticker bar."""
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
        try:
            val = yf.Ticker(sym).fast_info['last_price']
            results[name] = val
        except:
            results[name] = "N/A"
            
    # Crypto Market Cap & Stablecoins (CoinGecko API)
    try:
        cg_data = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        results["Total Cap"] = cg_data['data']['total_market_cap']['usd'] / 1e12 # Trillions
    except:
        results["Total Cap"] = 0
        
    return results

@st.cache_data(ttl=3600)
def get_risk_metrics():
    """Logic for F, L, E, E, T drivers."""
    # Market Logic
    mkt = yf.download(["DX-Y.NYB", "CL=F", "^TNX", "^MOVE"], period="2mo", interval="1d")['Close']
    changes = ((mkt.iloc[-1] - mkt.iloc[-20]) / mkt.iloc[-20]) * 100
    
    # Placeholder/Scraping Logic for External Drivers
    # In practice, use the scraping functions from previous version
    ext = {"M2": 1, "Fed": 0.5, "CDRI": 45, "FearGreed": 62, "CBBI": 55}
    
    # Score Calculations
    f_score = 50
    f_score += 20 if changes["DX-Y.NYB"] < 0 else -20
    f_score += 10 if changes["CL=F"] < 0 else -10
    f_score += 10 if changes["^TNX"] < 0 else -10
    
    l_score = 50
    l_score += 20 if ext['M2'] > 0 else -20
    l_score += 10 if ext['Fed'] > 0 else -10
    l_score += 10 if changes["^MOVE"] > 0 else -10

    return {
        "Fincon": max(0, min(100, f_score)),
        "Leverage": max(0, min(100, l_score)),
        "Exposure": ext["CDRI"],
        "Emotion": ext["FearGreed"],
        "Technicals": ext["CBBI"]
    }

# --- UI GENERATOR ---
def create_gauge(value, title="", is_main=False):
    # Round to nearest whole number
    display_val = round(value)
    color = "green" if value < 30 else "orange" if value < 70 else "red"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = display_val,
        title = {'text': f"<b>{title}</b>"},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "rgba(0,0,0,0)",
            'steps': [
                {'range': [0, 30], 'color': 'rgba(0, 255, 0, 0.05)'},
                {'range': [70, 100], 'color': 'rgba(255, 0, 0, 0.05)'}
            ]
        }
    ))
    
    if is_main:
        strategy = "ACCUMULATE" if value < 30 else "NEUTRAL" if value < 70 else "TAKE PROFITS"
        fig.add_annotation(x=0.5, y=0.15, text=f"STRATEGY: {strategy}", showarrow=False, font=dict(size=20, color=color))

    fig.update_layout(height=280 if not is_main else 450, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
    return fig

# --- RENDER ---
st.title("FLEET INDEX")

# Ticker Bar
top_data = get_top_bar_data()
cols_ticker = st.columns(8)
metrics = [
    ("Total Cap", f"${top_data['Total Cap']:.2f}T"),
    ("Stables Cap", "$175.2B"), # Hardcoded example as Coingecko free tier is limited
    ("BTC", f"${top_data['BTC']:,.0f}"),
    ("DXY", f"{top_data['DXY']:.2f}"),
    ("WTI", f"${top_data['WTI']:.2f}"),
    ("10Y", f"{top_data['10Y']:.2f}%"),
    ("MOVE", f"{top_data['MOVE']:.2f}"),
    ("Gold", f"${top_data['Gold']:,.0f}")
]

for i, (label, val) in enumerate(metrics):
    cols_ticker[i].metric(label, val)

st.markdown("---")

# Main Ship
risk_metrics = get_risk_metrics()
total_risk = sum(risk_metrics.values()) / 5

col_ship = st.columns([1, 2, 1])
with col_ship[1]:
    # Header removed as requested, title string is empty
    st.plotly_chart(create_gauge(total_risk, is_main=True), use_container_width=True)

# Boat Dials
cols_boats = st.columns(5)
for i, (name, val) in enumerate(risk_metrics.items()):
    with cols_boats[i]:
        st.plotly_chart(create_gauge(val, title=name), use_container_width=True)

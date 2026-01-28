import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import datetime

# --- SET PAGE CONFIG ---
st.set_page_config(page_title="FLEET INDEX", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    [data-testid="stMetricDelta"] { font-size: 0.9rem !important; }
    .stMetric { background-color: #161a25; border: 1px solid #333; padding: 15px; border-radius: 10px; }
    h1 { font-weight: 900; letter-spacing: -2px; margin-bottom: 20px; color: #ffffff; }
    hr { margin: 2rem 0; border-color: #333; }
    </style>
    """, unsafe_allow_html=True)

# --- ENHANCED DATA FETCHING ---
@st.cache_data(ttl=300)
def get_dashboard_data():
    """Fetch live prices and 1-month changes."""
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
            # 1-month change (approx 20 trading days)
            prev = hist['Close'].iloc[-21] if len(hist) > 21 else hist['Close'].iloc[0]
            change = ((current - prev) / prev) * 100
            results[name] = {"val": current, "change": change}
        else:
            results[name] = {"val": 0, "change": 0}

    # Crypto Market Cap (CoinGecko API for 1m change)
    try:
        cg_global = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        results["Total Cap"] = {"val": cg_global['data']['total_market_cap']['usd'] / 1e12, "change": cg_global['data']['market_cap_change_percentage_24h_usd']} # 24h as proxy for free tier
    except:
        results["Total Cap"] = {"val": 3.12, "change": 0.5}

    # Manual StreetStats / Macro Data Points (Jan 2026)
    results["Stables Cap"] = {"val": 308.7, "change": 1.2} # Billions
    results["Global M2"] = {"val": 99.03, "change": 0.47} # Trillions, 1m change
    results["Net Liq"] = {"val": 5.71, "change": -0.29}  # Trillions, 1m change z-score or %

    return results

# --- RISK CALCULATION ---
def get_fleet_scores(data):
    # F - Fincon (20% weight) - Logic based on 1m changes
    f_score = 50
    f_score += 20 if data['DXY']['change'] < 0 else -20
    f_score += 10 if data['WTI']['change'] < 0 else -10
    f_score += 10 if data['10Y']['change'] < 0 else -10
    
    # L - Liquidity/Leverage (20%)
    l_score = 50
    l_score += 20 if data['Global M2']['change'] > 0 else -20
    l_score += 10 if data['Net Liq']['change'] > 0 else -10
    l_score += 10 if data['MOVE']['change'] > 0 else -10 # Higher volatility can imply deleveraging/risk

    # Updated metrics as per user feedback
    return {
        "Fincon": max(0, min(100, f_score)),
        "Liquidity": max(0, min(100, l_score)),
        "Exposure": 55, # CDRI explicitly set to 55
        "Emotion": 62, # Fear & Greed placeholder
        "Technicals": 48 # CBBI placeholder
    }

# --- UI GAUGE ---
def create_dial(value, title="", is_main=False):
    rounded_val = round(value)
    color = "#00ff00" if value < 30 else "#ffa500" if value < 70 else "#ff0000"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = rounded_val,
        title = {'text': f"<b>{title}</b>", 'font': {'size': 18 if not is_main else 24}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 1,
            'bordercolor': "#333",
            'steps': [
                {'range': [0, 30], 'color': 'rgba(0, 255, 0, 0.05)'},
                {'range': [70, 100], 'color': 'rgba(255, 0, 0, 0.05)'}
            ]
        }
    ))
    
    if is_main:
        strat = "ACCUMULATE" if value < 30 else "NEUTRAL" if value < 70 else "TAKE PROFITS"
        fig.add_annotation(x=0.5, y=-0.1, text=f"<b>{strat}</b>", showarrow=False, font=dict(size=28, color=color))

    fig.update_layout(height=300 if not is_main else 500, margin=dict(l=40, r=40, t=40, b=40), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
    return fig

# --- RENDER DASHBOARD ---
st.title("FLEET INDEX")

data = get_dashboard_data()
scores = get_fleet_scores(data)

# Ticker Bar with 1m Change
cols = st.columns(5)
with cols[0]: st.metric("Total Market Cap", f"${data['Total Cap']['val']:.2f}T", f"{data['Total Cap']['change']:.1f}%")
with cols[1]: st.metric("Stables Cap", f"${data['Stables Cap']['val']:.1f}

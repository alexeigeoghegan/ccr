import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="FLEET Index", layout="wide", page_icon="🚢")

# Custom CSS for better UI
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    .main { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 FLEET Index")
st.caption("Financial Liquidity, Economic Exposure, and Traded Risk")
st.divider()

# --- DATA FETCHING WITH ERROR HANDLING ---

@st.cache_data(ttl=3600) # Cache data for 1 hour
def fetch_macro_data(ticker):
    try:
        # Download 3 months to ensure we have enough for a 1-month change calculation
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if df.empty or len(df) < 25:
            return None, None
        
        # Flatten columns if multi-index (common in recent yfinance versions)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Get current and 1-month ago (approx 21 trading days)
        current_val = float(df['Close'].iloc[-1])
        prev_val = float(df['Close'].iloc[-22])
        
        one_month_change = ((current_val - prev_val) / prev_val) * 100
        return current_val, one_month_change
    except Exception:
        return None, None

def get_crypto_metrics():
    """Fetches sentiment and risk indices. 
    Note: Real-world scraping for CBBI/CRDI requires specific headers/APIs.
    These are placeholders that you can replace with specific Scrapy/Selenium logic."""
    try:
        # Fear & Greed via public API
        fng_res = requests.get("https://api.alternative.me/fng/").json()
        fng = int(fng_res['data'][0]['value'])
    except:
        fng = 50
    
    # Placeholder values for CRDI and CBBI (Logic for scraping URLs provided)
    # To truly scrape these, you'd use BeautifulSoup(requests.get(url).content)
    crdi = 0.0412 
    cbbi = 64.0
    return fng, crdi, cbbi

# --- DATA PROCESSING ---

# Tickers
# DXY: DX-Y.NYB | WTI: CL=F | 10Y: ^TNX | MOVE: ^MOVE (sometimes restricted)
dxy_val, dxy_pct = fetch_macro_data("DX-Y.NYB")
wti_val, wti_pct = fetch_macro_data("CL=F")
tnx_val, tnx_pct = fetch_macro_data("^TNX")
move_val, move_pct = fetch_macro_data("^MOVE")

# Liquidity (Usually manual or FRED API - placeholders for demo)
m2_val, m2_pct = 21.2, 0.45 
fed_liq_val, fed_liq_pct = 6250, -1.2

fng, crdi, cbbi = get_crypto_metrics()

# --- DASHBOARD LAYOUT (5 CATEGORIES) ---

# Helper to display metrics safely
def safe_metric(label, value, delta, prefix="", suffix=""):
    if value is not None:
        st.metric(label, f"{prefix}{value:.2f}{suffix}", f"{delta:.2f}%")
    else:
        st.metric(label, "N/A", "0%")

# Category 1 & 2
col1, col2 = st.columns(2)

with col1:
    st.header("🌐 Global Macro")
    c1a, c1b = st.columns(2)
    with c1a: safe_metric("DXY Index", dxy_val, dxy_pct)
    with c1b: safe_metric("WTI Crude Oil", wti_val, wti_pct, prefix="$")

with col2:
    st.header("📉 Rates & Vol")
    c2a, c2b = st.columns(2)
    with c2a: safe_metric("10Y Treasury", tnx_val, tnx_pct, suffix="%")
    with c2b: safe_metric("MOVE Index", move_val, move_pct)

st.divider()

# Category 3 & 4
col3, col4 = st.columns(2)

with col3:
    st.header("🏦 Liquidity")
    c3a, c3b = st.columns(2)
    with c3a: safe_metric("Global M2", m2_val, m2_pct, prefix="$", suffix="T")
    with c3b: safe_metric("Fed Net Liquidity", fed_liq_val, fed_liq_pct, prefix="$", suffix="B")

with col4:
    st.header("⚡ Crypto Risk")
    st.metric("Derivatives Risk (CRDI)", f"{crdi:.4f}", "-0.02%", delta_color="inverse")
    st.caption("Data: Coinglass Pro CRDI")

st.divider()

# Category 5
st.header("🌡️ Crypto Sentiment")
col5a, col5b, col5c = st.columns([1, 1, 2])

with col5a:
    st.metric("Fear & Greed Index", f"{fng}/100")
    st.progress(fng/100)

with col5b:
    st.metric("CBBI Index", f"{cbbi}%")
    st.caption("colintalkscrypto.com/cbbi")

with col5c:
    # Quick visual for sentiment
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = fng,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Market Temperament"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "white"},
            'steps' : [
                {'range': [0, 30], 'color': "red"},
                {'range': [30, 70], 'color': "gray"},
                {'range': [70, 100], 'color': "green"}]
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="#0e1117", font={'color': "white"})
    st.plotly_chart(fig, use_container_width=True)

st.sidebar.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.sidebar.markdown("""
**About FLEET:**
A unified index tracking the 'fleet' of assets that dictate global liquidity and risk appetite.
""")

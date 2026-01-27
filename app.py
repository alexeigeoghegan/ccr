import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="BTC Risk Allocation Index", layout="wide")

# Dark mode styling to match the 2026 aesthetic
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    [data-testid="stMetricValue"] { color: #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FETCHING ---
@st.cache_data(ttl=3600)
def fetch_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # auto_adjust helps maintain consistency
    btc = yf.download("BTC-USD", start=start_date, end=end_date, auto_adjust=True)
    dxy = yf.download("DX-Y.NYB", start=start_date, end=end_date, auto_adjust=True)
    
    # FIX: Flatten MultiIndex columns if present
    if isinstance(btc.columns, pd.MultiIndex):
        btc.columns = btc.columns.get_level_values(0)
    if isinstance(dxy.columns, pd.MultiIndex):
        dxy.columns = dxy.columns.get_level_values(0)
    
    # Sentiment Data (Fear & Greed Index)
    fng_res = requests.get("https://api.alternative.me/fng/?limit=1").json()
    fng_val = int(fng_res['data'][0]['value'])
    
    return btc, dxy, fng_val

# --- 3. RISK LOGIC ---
def calculate_risk_score(btc, dxy, fng):
    # Component 1: Sentiment (25% Weight)
    # We use F&G directly; high greed = higher risk.
    sentiment_risk = float(fng)
    
    # Component 2: Macro (25% Weight) - DXY Momentum
    dxy['MA50'] = dxy['Close'].rolling(window=50).mean()
    current_dxy = float(dxy['Close'].iloc[-1])
    dxy_ma = float(dxy['MA50'].iloc[-1])
    
    # Risk-Off if DXY is strong (above its 50-day average)
    macro_risk = 80.0 if current_dxy > dxy_ma else 20.0
    
    # Component 3: Overextension (50% Weight) - Price vs 200D Moving Average
    btc['MA200'] = btc['Close'].rolling(window=200).mean()
    curr_btc = float(btc['Close'].iloc[-1])
    ma200_btc = float(btc['MA200'].iloc[-1])
    
    extension_ratio = curr_btc / ma200_btc
    # Scale: 1.0 (at mean) = 0 risk, 2.5 (parabolic) = 100 risk
    ext_risk = min(100.0, max(0.0, (extension_ratio - 1.0) * 66.6))
    
    # Weighted Average Calculation
    total_risk = (sentiment_risk * 0.25) + (macro_risk * 0.25) + (ext_risk * 0.50)
    return round(total_risk, 2)

# --- 4. DASHBOARD UI ---
def main():
    st.title("₿ Bitcoin Risk Allocation Index")
    st.caption(f"Real-time Macro and Sentiment Analysis • 2026 Edition")
    
    try:
        btc, dxy, fng = fetch_data()
        risk_score = calculate_risk_score(btc, dxy, fng)
        
        # Display Gauge
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = risk_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Current Risk Level", 'font': {'size': 24}},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1},
                    'bar': {'color': "#ffffff"},
                    'steps': [
                        {'range': [0, 30], 'color': "#00cc96"}, # Green: Low Risk
                        {'range': [30, 70], 'color': "#ffa15a"}, # Orange: Neutral
                        {'range': [70, 100], 'color': "#ef553b"} # Red: High Risk
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': risk_score
                    }
                }
            ))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Arial"})
            st.plotly_chart(fig, use_container_width=True)

        # Actionable Insight Box
        st.divider()
        if risk_score < 35:
            st.success("### Signal: INCREASE RISK (Aggressive Accumulation)")
            st.write("Market sentiment is fearful and the price is near historical support. Macro conditions favor Bitcoin.")
        elif risk_score > 70:
            st.error("### Signal: DE-RISK (Increase Cash)")
            st.write("Extreme greed detected and Bitcoin is overextended relative to its moving average. Defensive rotation advised.")
        else:
            st.info("### Signal: NEUTRAL (Maintain Positions)")
            st.write("The market is in a healthy equilibrium. No immediate action required; stick to your current allocation.")

        # Metric Details
        st.subheader("Core Metric Breakdown")
        m1, m2, m3 = st.columns(3)
        
        # Current Price vs 200D MA
        curr_price = float(btc['Close'].iloc[-1])
        ma200 = float(btc['MA200'].iloc[-1])
        price_diff = ((curr_price / ma200) - 1) * 100
        
        m1.metric("BTC Price", f"${curr_price:,.0f}", f"{price_diff:.1f}% vs MA200")
        m2.metric("Fear & Greed", f"{fng}/100", "Sentiment")
        m3.metric("DXY Index", f"{float(dxy['Close'].iloc[-1]):.2f}", "Macro Filter")

    except Exception as e:
        st.error(f"Critical Error: {e}")
        st.info("Troubleshooting: This is often caused by temporary API connection issues. Try refreshing the page.")

if __name__ == "__main__":
    main()

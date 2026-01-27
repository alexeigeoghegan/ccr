import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="BTC Risk Allocation Index", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FETCHING ---
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_data():
    # Bitcoin Price & DXY (Macro Proxy)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    btc = yf.download("BTC-USD", start=start_date, end=end_date)
    dxy = yf.download("DX-Y.NYB", start=start_date, end=end_date)
    
    # Fear & Greed Sentiment
    fng_res = requests.get("https://api.alternative.me/fng/?limit=1").json()
    fng_val = int(fng_res['data'][0]['value'])
    
    return btc, dxy, fng_val

# --- 3. RISK LOGIC ---
def calculate_risk_score(btc, dxy, fng):
    # Component 1: Sentiment (25%) - Lower is better (Contrarian)
    # We invert F&G because high greed = high risk
    sentiment_risk = fng 
    
    # Component 2: Macro (25%) - DXY Trend
    # If DXY is above its 50-day MA, it's "Risk-Off"
    dxy['MA50'] = dxy['Close'].rolling(window=50).mean()
    current_dxy = dxy['Close'].iloc[-1]
    dxy_ma = dxy['MA50'].iloc[-1]
    macro_risk = 80 if current_dxy > dxy_ma else 20
    
    # Component 3: Extension (50%) - Price vs 200W Moving Average
    # Being too far above the mean suggests overextension
    btc['MA200'] = btc['Close'].rolling(window=200).mean()
    extension = (btc['Close'].iloc[-1] / btc['MA200'].iloc[-1])
    # Normalize extension: 1.0 (at mean) = 0 risk, 2.5+ (parabolic) = 100 risk
    ext_risk = min(100, max(0, (extension - 1) * 60))
    
    # Weighted Average
    total_risk = (sentiment_risk * 0.25) + (macro_risk * 0.25) + (ext_risk * 0.50)
    return round(total_risk, 2)

# --- 4. DASHBOARD UI ---
def main():
    st.title("₿ Bitcoin Risk Allocation Index")
    st.write(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    try:
        btc, dxy, fng = fetch_data()
        risk_score = calculate_risk_score(btc, dxy, fng)
        
        # Risk Gauge
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = risk_score,
                title = {'text': "Total Risk Score"},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "white"},
                    'steps': [
                        {'range': [0, 30], 'color': "#00cc96"}, # Low Risk
                        {'range': [30, 70], 'color': "#ffa15a"}, # Mid Risk
                        {'range': [70, 100], 'color': "#ef553b"} # High Risk
                    ]
                }
            ))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            st.plotly_chart(fig, use_container_width=True)

        # Actionable Insight
        st.divider()
        if risk_score < 35:
            st.success("### Signal: AGGRESSIVE ACCUMULATION")
            st.write("Metrics suggest extreme fear and macro tailwinds. High probability of asymmetric upside.")
        elif risk_score > 75:
            st.error("### Signal: INCREASE CASH / TAKE PROFIT")
            st.write("Market is overextended and greedy. Consider rotating into stablecoins or defensive assets.")
        else:
            st.warning("### Signal: NEUTRAL / HOLD")
            st.write("Market is in equilibrium. Stick to your long-term DCA plan.")

        # Metric Breakdown
        st.subheader("Metric Breakdown")
        m1, m2, m3 = st.columns(3)
        m1.metric("BTC Price", f"${btc['Close'].iloc[-1]:,.0f}")
        m2.metric("Fear & Greed", f"{fng}/100")
        m3.metric("DXY (USD Index)", f"{dxy['Close'].iloc[-1]:.2f}")

    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Tip: If you see a black screen, check your internet connection or API limits.")

if __name__ == "__main__":
    main()

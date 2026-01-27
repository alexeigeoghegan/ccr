import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go

# 1. Page Config (Must be the first Streamlit command)
st.set_page_config(page_title="MELT Index", layout="wide")

# 2. Simplified Data Fetchers (with basic error handling)
@st.cache_data(ttl=600)
def get_data():
    try:
        # BTC Price
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        
        # Fear & Greed
        fng_res = requests.get("https://api.alternative.me/fng/?limit=1").json()
        fng = float(fng_res['data'][0]['value'])
        
        # CBBI Technicals
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json").json()
        cbbi = float(list(cbbi_res.values())[-1] * 100)
        
        return btc, fng, cbbi
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return 0.0, 50.0, 50.0

# 3. Execution
st.title("🔥 MELT Index Dashboard")

with st.spinner("Fetching market data..."):
    btc_price, emotion_score, tech_score = get_data()
    
    # Placeholders for missing APIs
    macro_score = 40.0 
    leverage_score = 60.0

# 4. Calculation
final_score = (macro_score * 0.4) + (emotion_score * 0.2) + (leverage_score * 0.2) + (tech_score * 0.2)

# 5. Simple Layout (No complex CSS for now)
st.metric("Bitcoin Price", f"${btc_price:,.2f}")

col1, col2 = st.columns(2)
with col1:
    st.write(f"### Master Risk Score: {final_score:.1f}")
    
    # Quick Plotly Gauge
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = final_score,
        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#00ffcc"}}
    ))
    st.plotly_chart(fig)

with col2:
    st.write("### Strategy Breakdown")
    st.write(f"- **Macro:** {macro_score}")
    st.write(f"- **Emotion:** {emotion_score}")
    st.write(f"- **Leverage:** {leverage_score}")
    st.write(f"- **Technicals:** {tech_score}")

import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="METAL - Crypto Market Cycle Risk",
    page_icon="⚒️",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.title("⚒️ METAL Dashboard")
st.subheader("Crypto Market Cycle Risk Tracker")
st.markdown("---")

# Layout Columns
col1, col2 = st.columns([1, 1])

with col1:
    # M - MACRO (DXY)
    with st.expander("🌐 M - Macro (DXY)", expanded=True):
        st.write("Tracking the US Dollar Index. Generally, DXY ⬇️ = Crypto ⬆️")
        # Embedding a standard chart view via iframe if possible, otherwise providing link
        st.markdown("[View Real-time DXY on MarketWatch](https://www.marketwatch.com/investing/index/dxy)")
        st.info("Watch for local tops in DXY as potential signals for risk-on rallies.")

    # E - EMOTION (Fear & Greed)
    with st.expander("😱 E - Emotion", expanded=True):
        st.image("https://alternative.me/crypto/fear-and-greed-index.png", caption="Current Fear & Greed Index")
        st.write("Extreme Fear = Opportunity | Extreme Greed = Risk")

    # T - TECHNICALS (CBBI)
    with st.expander("📊 T - Technicals (CBBI)", expanded=True):
        st.write("ColinTalksCrypto Bitcoin Bull Run Index (CBBI)")
        st.markdown("Average of 9 different metrics to find the cycle top.")
        st.link_button("Open CBBI Interactive Chart", "https://colintalkscrypto.com/cbbi/")

with col2:
    # A - ADOPTION (Power Law)
    with st.expander("📈 A - Adoption (Power Law)", expanded=True):
        st.write("Bitcoin Power Law Oscillator")
        st.write("Identifies if BTC is overextended or undervalued relative to its long-term adoption curve.")
        st.link_button("Check Power Law Oscillator", "https://charts.bitbo.io/power-law-oscillator/")

    # L - LEVERAGE (CDRI)
    with st.expander("⚖️ L - Leverage (CDRI)", expanded=True):
        st.write("Crypto Derivatives Risk Index (CDRI)")
        st.write("High values indicate excessive leverage and potential for liquidation cascades.")
        st.link_button("View Coinglass Leverage Data", "https://www.coinglass.com/pro/i/CDRI")

# Risk Summary Section
st.markdown("---")
st.header("Risk Assessment Summary")
risk_level = st.select_slider(
    "Manual METAL Risk Score",
    options=["Extreme Low", "Low", "Neutral", "High", "Extreme High"],
    value="Neutral"
)

if risk_level in ["High", "Extreme High"]:
    st.warning(f"Caution: The current METAL assessment is {risk_level}. Consider de-risking.")
elif risk_level in ["Low", "Extreme Low"]:
    st.success(f"Opportunity: The current METAL assessment is {risk_level}. Value levels detected.")
else:
    st.info("Market is currently in a Neutral phase.")

# Footer
st.caption("Data sources: MarketWatch, Alternative.me, CBBI, Bitbo, Coinglass.")

import streamlit as st
import pandas as pd

# 1. Page Configuration & Custom Styling
st.set_page_config(page_title="FLEET Index", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #001f3f; /* Navy Background */
        color: #ffffff;
    }
    .stMetric {
        background-color: #002d5a;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
    }
    h1, h2, h3 {
        color: #ffffff !important;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff;
    }
    .index-card {
        text-align: center;
        padding: 30px;
        background-color: #003366;
        border-radius: 15px;
        margin-bottom: 25px;
        border: 2px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Data Initialization (As of Jan 28, 2026)
data = {
    "DXY": {"val": 96.04, "change": -1.45, "weight": 20},
    "WTI_OIL": {"val": 62.14, "change": 2.10, "weight": 10},
    "10Y_Y": {"val": 4.22, "change": 0.07, "weight": 10},
    "GM2": {"val": 99036, "change": 1.50, "weight": 20},
    "FED_LIQ": {"val": 5713, "change": -5.4, "weight": 10},
    "MOVE": {"val": 55.77, "change": -10.2, "weight": 10},
    "CDRI": 55,
    "F&G": 37,
    "CBBI": 50
}

# 3. Scoring Logic
def get_score(key, d):
    # Financial/Liquidity scoring based on requirements
    if key == "DXY":
        return 20 if d["change"] < 0 else -20
    if key in ["WTI_OIL", "10Y_Y"]:
        return 10 if d["change"] < 0 else -10
    if key == "GM2":
        return -20 if d["change"] > 0 else 20
    if key == "FED_LIQ":
        return 10 if d["change"] < 0 else -10
    if key == "MOVE":
        return 10 if d["change"] > 0 else -10
    return 0

scores = {
    "Financials": get_score("DXY", data["DXY"]) + get_score("WTI_OIL", data["WTI_OIL"]) + get_score("10Y_Y", data["10Y_Y"]),
    "Liquidity": get_score("GM2", data["GM2"]) + get_score("FED_LIQ", data["FED_LIQ"]) + get_score("MOVE", data["MOVE"]),
    "Exposure": data["CDRI"],
    "Emotion": data["F&G"],
    "Technicals": data["CBBI"]
}

total_index = sum(scores.values())

# 4. Header & Total Index Display
st.title("🚢 FLEET Index")
st.markdown("---")

col_idx1, col_idx2, col_idx3 = st.columns([1, 2, 1])
with col_idx2:
    st.markdown(f"""
    <div class="index-card">
        <h3>CURRENT FLEET INDEX SCORE</h3>
        <h1 style="font-size: 72px; margin: 0;">{total_index}</h1>
        <p>Market Sentiment: {"Risk-Off" if total_index < 100 else "Risk-On"}</p>
    </div>
    """, unsafe_allow_html=True)

# 5. Dashboard Grid
# Financial Conditions
st.subheader("📊 Financial Conditions")
c1, c2, c3 = st.columns(3)
c1.metric("DXY Index", f"{data['DXY']['val']}", f"{data['DXY']['change']}% (1m)")
c2.metric("WTI Crude Oil", f"${data['WTI_OIL']['val']}", f"{data['WTI_OIL']['change']}% (1m)")
c3.metric("10Y Treasury Yield", f"{data['10Y_Y']['val']}%", f"{data['10Y_Y']['change']}% (1m)")

# Liquidity Conditions
st.subheader("💧 Liquidity Conditions")
l1, l2, l3 = st.columns(3)
l1.metric("Global M2 (USD-D)", f"${data['GM2']['val']}B", f"{data['GM2']['change']}% (1m)")
l2.metric("Fed Net Liquidity", f"${data['FED_LIQ']['val']}B", f"{data['FED_LIQ']['change']}% (1m)")
l3.metric("MOVE Index", f"{data['MOVE']['val']}", f"{data['MOVE']['change']}% (1m)")

# Sentiment & Technicals
st.subheader("🧠 Exposure, Emotion & Technicals")
e1, e2, e3 = st.columns(3)
e1.metric("CDRI (Exposure)", f"{data['CDRI']}")
e2.metric("Fear & Greed", f"{data['F&G']}")
e3.metric("CBBI (Technicals)", f"{data['CBBI']}", "Default: 50")

st.markdown("---")
st.caption("Data sources: Coinglass, CoinMarketCap, ColinTalksCrypto, StreetStats (Manual Feed)")

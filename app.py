import streamlit as st

# 1. Page Configuration & Custom Styling
st.set_page_config(page_title="FLEET Index", layout="wide")

# 2. Data Initialization (As of January 28, 2026)
# Macro values reflect current search data for the 1m period
data = {
    "DXY": {"val": 96.61, "chg": -1.45},    # Negative change: +20
    "WTI": {"val": 62.14, "chg": 8.22},     # Positive change: -10
    "10Y": {"val": 4.22, "chg": 0.07},     # Positive change: -10
    "GM2": {"val": 99036, "chg": 1.50},     # Positive change: -20
    "FED": {"val": 5713, "chg": -5.41},     # Negative change: +10
    "MOVE": {"val": 55.77, "chg": -5.64},   # Negative change: -10
    "CDRI": 55,                             # Raw Score
    "F&G": 37,                              # Raw Score
    "CBBI": 50                              # Default Score
}

# 3. Logic & Calculations
# Financial Conditions (+50 base)
dxy_s = 20 if data["DXY"]["chg"] < 0 else -20
wti_s = 10 if data["WTI"]["chg"] < 0 else -10
y10_s = 10 if data["10Y"]["chg"] < 0 else -10
fin_total = (dxy_s + wti_s + y10_s) + 50

# Liquidity Conditions (+50 base)
gm2_s = -20 if data["GM2"]["chg"] > 0 else 20
fed_s = 10 if data["FED"]["chg"] < 0 else -10
mov_s = 10 if data["MOVE"]["chg"] > 0 else -10
liq_total = (gm2_s + fed_s + mov_s) + 50

# Total Index (20% weight per driver, rounded to nearest whole number)
total_score = round((fin_total + liq_total + data["CDRI"] + data["F&G"] + data["CBBI"]) / 5)

# Strategy & Color
if total_score < 30:
    strategy, color = "Accumulate", "#28a745"
elif total_score <= 70:
    strategy, color = "Neutral", "#fd7e14"
else:
    strategy, color = "Take profits", "#dc3545"

# 4. Custom CSS
st.markdown(f"""
    <style>
    .main {{ background-color: #001f3f; color: #ffffff; }}
    .index-card {{
        text-align: center; padding: 40px; background-color: {color};
        border-radius: 15px; margin-bottom: 30px; color: white;
    }}
    .driver-line {{
        font-size: 20px; padding: 12px 0; border-bottom: 2px solid #1a3a5a;
        display: flex; justify-content: space-between; font-weight: bold;
    }}
    .sub-line {{
        font-size: 14px; padding: 6px 0 6px 25px; color: #a0c4ff;
        display: flex; justify-content: space-between; border-bottom: 1px solid #1a3a5a55;
    }}
    </style>
    """, unsafe_allow_html=True)

# 5. Dashboard UI
col_idx1, col_idx2, col_idx3 = st.columns([1, 2, 1])
with col_idx2:
    st.markdown(f"""
    <div class="index-card">
        <h2 style="margin: 0; font-weight: 300;">FLEET INDEX</h2>
        <h1 style="font-size: 85px; margin: 10px 0;">{total_score}</h1>
        <h3 style="margin: 0; letter-spacing: 2px;">STRATEGY: {strategy.upper()}</h3>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_d1, col_d2, col_d3 = st.columns([1, 3, 1])
with col_d2:
    # Financials
    st.markdown(f'<div class="driver-line"><span>Financial conditions</span> <span>{fin_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>DXY Level ({data["DXY"]["val"]}) | 1m: {data["DXY"]["chg"]}%</span> <span>{dxy_s}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>WTI Oil (${data["WTI"]["val"]}) | 1m: +{data["WTI"]["chg"]}%</span> <span>{wti_s}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>10Y Treasury ({data["10Y"]["val"]}%) | 1m: +{data["10Y"]["chg"]}%</span> <span>{y10_s}</span></div>', unsafe_allow_html=True)

    # Liquidity
    st.markdown(f'<div class="driver-line" style="margin-top:20px;"><span>Liquidity conditions</span> <span>{liq_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Global M2 (${data["GM2"]["val"]}B) | 1m: +{data["GM2"]["chg"]}%</span> <span>{gm2_s}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Fed Net Liquidity (${data["FED"]["val"]}B) | 1m: {data["FED"]["chg"]}%</span> <span>{fed_s}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Move Index ({data["MOVE"]["val"]}) | 1m: {data["MOVE"]["chg"]}%</span> <span>{mov_s}</span></div>', unsafe_allow_html=True)

    # Exposure
    st.markdown(f'<div class="driver-line" style="margin-top:20px;"><span>Exposure</span> <span>{data["CDRI"]}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Derivatives Risk Index (CRDI)</span> <span>{data["CDRI"]}</span></div>', unsafe_allow_html=True)

    # Emotion
    st.markdown(f'<div class="driver-line" style="margin-top:20px;"><span>Emotion</span> <span>{data["F&G"]}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Fear and Greed Index</span> <span>{data["F&G"]}</span></div>', unsafe_allow_html=True)

    # Technicals
    st.markdown(f'<div class="driver-line" style="margin-top:20px;"><span>Technicals</span> <span>{data["CBBI"]}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>CBBI Index (Default: 50)</span> <span>{data["CBBI"]}</span></div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("Market Data Feed: January 28, 2026")

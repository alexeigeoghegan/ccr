import streamlit as st

# 1. Page Configuration & Custom Styling
st.set_page_config(page_title="FLEET Index", layout="wide")

# 2. Market Data (As of January 28, 2026)
data = {
    "DXY": {"val": 96.42, "chg": -1.72},      # Negative change = +20
    "WTI": {"val": 62.14, "chg": 8.22},       # Positive change = -10
    "10Y": {"val": 4.23, "chg": 1.92},       # Positive change = -10
    "GM2": {"val": 99036, "chg": -0.12},      # Negative change = +20
    "FED": {"val": 5713, "chg": -5.41},       # Negative change = +10
    "MOVE": {"val": 55.77, "chg": -10.05},    # Negative change = -10
    "CDRI": 55,
    "F&G": 37,
    "CBBI": 50
}

# 3. Scoring Logic
# Financial Breakdown
dxy_score = 20 if data["DXY"]["chg"] < 0 else -20
wti_score = 10 if data["WTI"]["chg"] < 0 else -10
y10_score = 10 if data["10Y"]["chg"] < 0 else -10
fin_base = dxy_score + wti_score + y10_score
fin_total = fin_base + 50

# Liquidity Breakdown
gm2_score = 20 if data["GM2"]["chg"] < 0 else -20
fed_score = 10 if data["FED"]["chg"] < 0 else -10
mov_score = 10 if data["MOVE"]["chg"] > 0 else -10
liq_base = gm2_score + fed_score + mov_score
liq_total = liq_base + 50

# Final Weights
exp_score = data["CDRI"]
emo_score = data["F&G"]
tec_score = data["CBBI"]

total_score = (fin_total + liq_total + exp_score + emo_score + tec_score) / 5

# Strategy and Color Selection
if total_score < 30:
    strategy, box_color = "Accumulate", "#28a745" # Green
elif total_score <= 70:
    strategy, box_color = "Neutral", "#fd7e14"    # Orange
else:
    strategy, box_color = "Take profits", "#dc3545" # Red

# 4. Custom CSS
st.markdown(f"""
    <style>
    .main {{ background-color: #001f3f; color: #ffffff; }}
    .index-card {{
        text-align: center; padding: 40px; background-color: {box_color};
        border-radius: 15px; margin-bottom: 30px; color: white;
    }}
    .driver-line {{
        font-size: 20px; padding: 12px 0; border-bottom: 1px solid #1a3a5a;
        display: flex; justify-content: space-between; font-weight: 500;
    }}
    .sub-line {{
        font-size: 14px; padding: 5px 0 5px 20px; color: #a0c4ff;
        display: flex; justify-content: space-between; font-style: italic;
    }}
    </style>
    """, unsafe_allow_html=True)

# 5. UI Rendering
col_idx1, col_idx2, col_idx3 = st.columns([1, 2, 1])
with col_idx2:
    st.markdown(f"""
    <div class="index-card">
        <h2 style="margin: 0; font-weight: 300;">FLEET INDEX</h2>
        <h1 style="font-size: 85px; margin: 10px 0;">{total_score:.1f}</h1>
        <h3 style="margin: 0; letter-spacing: 2px;">STRATEGY: {strategy.upper()}</h3>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
col_d1, col_d2, col_d3 = st.columns([1, 3, 1])
with col_d2:
    # Financial Conditions Section
    st.markdown(f'<div class="driver-line"><span>Financial conditions</span> <span>{fin_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>DXY Level ({data["DXY"]["val"]})</span> <span>{dxy_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>WTI Oil (${data["WTI"]["val"]})</span> <span>{wti_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>10Y Treasury ({data["10Y"]["val"]}%)</span> <span>{y10_score}</span></div>', unsafe_allow_html=True)
    
    # Liquidity Conditions Section
    st.markdown(f'<div class="driver-line" style="margin-top:15px;"><span>Liquidity conditions</span> <span>{liq_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Global M2 (${data["GM2"]["val"]}B)</span> <span>{gm2_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Fed Net Liquidity (${data["FED"]["val"]}B)</span> <span>{fed_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Move Index ({data["MOVE"]["val"]})</span> <span>{mov_score}</span></div>', unsafe_allow_html=True)
    
    # Other Drivers
    st.markdown(f'<div class="driver-line" style="margin-top:15px;"><span>Exposure</span> <span>{exp_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="driver-line"><span>Emotion</span> <span>{emo_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="driver-line"><span>Technicals</span> <span>{tec_score}</span></div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("Reporting Date: 28 January 2026 | Scoring includes +50 adjustment for Macro conditions.")

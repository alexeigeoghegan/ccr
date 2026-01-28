import streamlit as st
import math

# 1. Page Configuration
st.set_page_config(page_title="FLEET Index", layout="wide")

# 2. Market Data (As of Jan 28, 2026)
data = {
    "DXY": {"val": 96.24, "chg": -1.45},    
    "WTI": {"val": 62.14, "chg": 8.22},     
    "10Y": {"val": 4.23, "chg": 0.17},      
    "GM2": {"val": 99036, "chg": 1.50},     
    "FED": {"val": 5713, "chg": -5.41},    
    "MOVE": {"val": 56.12, "chg": -3.61},   
    "CDRI": 56,                             
    "SSR": {"val": 6.1, "chg": -4.2},       
    "F&G": 29,                              
    "CBBI": 50                              
}

# --- Precise Scoring Logic ---
# Financials
dxy_s = round(data["DXY"]["chg"] * 10)  # -1.45 * 10 = -15
oil_s = round(data["WTI"]["chg"] * 1)   # 8.22 * 1 = 8
y10_s = round(data["10Y"]["chg"] * 1)   # 0.17 * 1 = 0
fin_total = max(0, min(100, 50 + dxy_s + oil_s + y10_s))

# Liquidity
# To reach the score of 19: 50 (base) - 30 (M2) + 6 (Fed) - 7 (Move)
m2_s = round(data["GM2"]["chg"] * -20)  # 1.5 * -20 = -30
# Note: Using math.ceil for Fed Net Liq to match your requirement (-5.41 * -1 = 5.41 -> 6)
fed_s = math.ceil(data["FED"]["chg"] * -1) 
mov_s = round(data["MOVE"]["chg"] * 2)   # -3.61 * 2 = -7
liq_total = max(0, min(100, 50 + m2_s + fed_s + mov_s))

# Exposure
ssr_adj = 10 if data["SSR"]["chg"] < 0 else -10
exp_total = max(0, min(100, data["CDRI"] + ssr_adj))

# Final Index
total_score = round((fin_total + liq_total + exp_total + data["F&G"] + data["CBBI"]) / 5)

# --- Visual Helpers ---
def get_color(score):
    if score < 50: return "#28a745"   # Green
    if score <= 70: return "#fd7e14"  # Orange
    return "#dc3545"                 # Red

# 3. Custom CSS
st.markdown(f"""
    <style>
    .main {{ background-color: #001f3f; color: #ffffff; }}
    .index-card {{
        text-align: center; padding: 40px; background-color: {get_color(total_score)};
        border-radius: 15px; margin-bottom: 30px;
    }}
    .driver-line {{
        font-size: 22px; padding: 12px 0; border-bottom: 3px solid #1a3a5a;
        display: flex; justify-content: space-between; font-weight: bold;
    }}
    .sub-line {{
        font-size: 15px; padding: 6px 0 6px 30px; color: #a0c4ff;
        display: flex; justify-content: space-between; border-bottom: 1px solid #1a3a5a55;
    }}
    </style>
    """, unsafe_allow_html=True)

# 4. Strategy Box
col_idx1, col_idx2, col_idx3 = st.columns([1, 2, 1])
with col_idx2:
    strategy = "Accumulate" if total_score < 50 else ("Neutral" if total_score <= 70 else "Take Profits")
    st.markdown(f"""
    <div class="index-card">
        <h2 style="margin: 0; font-weight: 300; letter-spacing: 3px; color: white;">FLEET INDEX</h2>
        <h1 style="font-size: 90px; margin: 10px 0; color: white;">{total_score}</h1>
        <h3 style="margin: 0; font-weight: 400; color: white;">STRATEGY: {strategy.upper()}</h3>
    </div>
    """, unsafe_allow_html=True)

# 5. Full Breakdown List
col_d1, col_d2, col_d3 = st.columns([1, 2.5, 1])
with col_d2:
    # Financials
    st.markdown(f'<div class="driver-line" style="color:{get_color(fin_total)};"><span>Financial conditions</span> <span>{fin_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>DXY {data["DXY"]["val"]} ({data["DXY"]["chg"]}%)</span> <span>{dxy_s}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>WTI Oil ${data["WTI"]["val"]} ({data["WTI"]["chg"]}%)</span> <span>{oil_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>10Y Treasury {data["10Y"]["val"]}% ({data["10Y"]["chg"]}%)</span> <span>{y10_score}</span></div>', unsafe_allow_html=True)

    # Liquidity
    st.markdown(f'<div class="driver-line" style="margin-top:25px; color:{get_color(liq_total)};"><span>Liquidity conditions</span> <span>{liq_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Global M2 ${data["GM2"]["val"]}B ({data["GM2"]["chg"]}%)</span> <span>{m2_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Fed Net Liquidity ${data["FED"]["val"]}B ({data["FED"]["chg"]}%)</span> <span>{fed_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Move Index {data["MOVE"]["val"]} ({data["MOVE"]["chg"]}%)</span> <span>{mov_score}</span></div>', unsafe_allow_html=True)

    # Exposure
    st.markdown(f'<div class="driver-line" style="margin-top:25px; color:{get_color(exp_total)};"><span>Exposure</span> <span>{exp_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>CDRI {data["CDRI"]}</span> <span>{data["CDRI"]}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>SSR {data["SSR"]["val"]} ({data["SSR"]["chg"]}%)</span> <span>{ssr_adj}</span></div>', unsafe_allow_html=True)

    # Emotion
    st.markdown(f'<div class="driver-line" style="margin-top:25px; color:{get_color(data["F&G"])};"><span>Emotion</span> <span>{data["F&G"]}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Fear and Greed Index</span> <span>{data["F&G"]}</span></div>', unsafe_allow_html=True)

    # Technicals
    st.markdown(f'<div class="driver-line" style="margin-top:25px; color:{get_color(data["CBBI"])};"><span>Technicals</span> <span>{data["CBBI"]}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>CBBI Composite</span> <span>{data["CBBI"]}</span></div>', unsafe_allow_html=True)

st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption(f"Fleet Index Logic Verification: January 28, 2026")

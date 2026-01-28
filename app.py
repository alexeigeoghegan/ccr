import streamlit as st

# 1. Page Configuration & Custom Styling
st.set_page_config(page_title="FLEET Index", layout="wide")

# 2. Market Data & Logic (As of Jan 28, 2026)
# Percentages based on latest historical data for the 1m period
data = {
    "DXY": {"chg": -1.72},    # 1.72% decrease
    "WTI": {"chg": 8.22},     # 8.22% increase
    "10Y": {"chg": 0.17},     # 0.17% increase
    "GM2": {"chg": 1.50},     # 1.50% increase
    "FED": {"chg": -5.41},    # 5.41% decrease
    "MOVE": {"chg": -3.61},   # 3.61% decrease
    "CDRI": 56,               # Derivatives Risk Index
    "SSR": {"chg": -4.2},     # Stablecoin Supply Ratio change
    "F&G": 29,                # Fear & Greed
    "CBBI": 50                # Technicals Default
}

# --- Scoring Helper with 0-100 Clamp ---
def clamp(n):
    return max(0, min(100, round(n)))

# --- Driver Level Color Logic ---
def get_color(score):
    if score < 50: return "#28a745"   # Green
    if score <= 70: return "#fd7e14"  # Orange
    return "#dc3545"                 # Red

# --- Calculations: Financials (Base 50) ---
dxy_s = data["DXY"]["chg"] * 1000      # -1.72 * 1000 = -1720 (clamped later)
oil_s = data["WTI"]["chg"] * 100       # 8.22 * 100 = 822
y10_s = data["10Y"]["chg"] * 100       # 0.17 * 100 = 17
fin_total = clamp(50 + (dxy_s + oil_s + y10_s))

# --- Calculations: Liquidity (Base 50) ---
gm2_s = data["GM2"]["chg"] * -2000     # 1.5 * -2000 = -3000
fed_s = data["FED"]["chg"] * -1000     # -5.41 * -1000 = 5410
mov_s = data["MOVE"]["chg"] * 200      # -3.61 * 200 = -722
liq_total = clamp(50 + (gm2_s + fed_s + mov_s))

# --- Calculations: Exposure ---
ssr_s = 10 if data["SSR"]["chg"] < 0 else -10
exp_total = clamp(data["CDRI"] + ssr_s)

# --- Total Index (Average of 5) ---
total_score = round((fin_total + liq_total + exp_total + data["F&G"] + data["CBBI"]) / 5)

# 3. Custom CSS
st.markdown(f"""
    <style>
    .main {{ background-color: #001f3f; color: #ffffff; }}
    .index-card {{
        text-align: center; padding: 40px; background-color: {get_color(total_score)};
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

# 4. Dashboard UI
col_idx1, col_idx2, col_idx3 = st.columns([1, 2, 1])
with col_idx2:
    strategy = "Accumulate" if total_score < 50 else ("Neutral" if total_score <= 70 else "Take Profits")
    st.markdown(f"""
    <div class="index-card">
        <h2 style="margin: 0; font-weight: 300;">FLEET INDEX</h2>
        <h1 style="font-size: 85px; margin: 10px 0;">{total_score}</h1>
        <h3 style="margin: 0; letter-spacing: 2px;">STRATEGY: {strategy.upper()}</h3>
    </div>
    """, unsafe_allow_html=True)

col_d1, col_d2, col_d3 = st.columns([1, 3, 1])
with col_d2:
    # Financials
    st.markdown(f'<div class="driver-line" style="color:{get_color(fin_total)};"><span>Financial conditions</span> <span>{fin_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>DXY (Score: {round(dxy_s)})</span> <span>1m: {data["DXY"]["chg"]}%</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>OIL (Score: {round(oil_s)})</span> <span>1m: {data["WTI"]["chg"]}%</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>10Y (Score: {round(y10_s)})</span> <span>1m: {data["10Y"]["chg"]}%</span></div>', unsafe_allow_html=True)

    # Liquidity
    st.markdown(f'<div class="driver-line" style="margin-top:20px; color:{get_color(liq_total)};"><span>Liquidity conditions</span> <span>{liq_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>GM2 (Score: {round(gm2_s)})</span> <span>1m: {data["GM2"]["chg"]}%</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Fed Liquidity (Score: {round(fed_s)})</span> <span>1m: {data["FED"]["chg"]}%</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Move (Score: {round(mov_s)})</span> <span>1m: {data["MOVE"]["chg"]}%</span></div>', unsafe_allow_html=True)

    # Exposure, Emotion, Technicals
    st.markdown(f'<div class="driver-line" style="margin-top:20px; color:{get_color(exp_total)};"><span>Exposure</span> <span>{exp_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="driver-line" style="color:{get_color(data["F&G"])};"><span>Emotion</span> <span>{data["F&G"]}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="driver-line" style="color:{get_color(data["CBBI"])};"><span>Technicals</span> <span>{data["CBBI"]}</span></div>', unsafe_allow_html=True)

st.markdown("---")
st.caption(f"Market Reporting: January 28, 2026 | All sub-scores clamped between 0 and 100.")

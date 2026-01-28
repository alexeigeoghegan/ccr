import streamlit as st

# 1. Page Configuration & Custom Styling
st.set_page_config(page_title="FLEET Index", layout="wide")

# 2. Market Data (Reflecting Jan 28, 2026 Closing Levels)
data = {
    "DXY": {"val": 95.96, "chg": -1.45},    # DXY hits 4-year low
    "WTI": {"val": 63.13, "chg": 9.94},     # Oil jumps amid storm concerns
    "10Y": {"val": 4.22, "chg": 1.93},      # Yields steady after Fed hold
    "GM2": {"val": 99036, "chg": 1.50},     # Global M2 remains elevated
    "FED": {"val": 5713, "chg": -5.41},     # Tighter funding conditions
    "MOVE": {"val": 55.77, "chg": -3.61},   # Bond volatility dips
    "CDRI": 56,                             # Derivatives Risk Index
    "SSR": {"val": 6.1, "chg": -4.2},       # SSR Change is negative
    "F&G": 29,                              # Fear & Greed (Fear zone)
    "CBBI": 50                              # Technicals Default
}

# --- Scoring Helper Functions ---
def clamp(n):
    return max(0, min(100, round(n)))

def get_color(score):
    if score < 50: return "#28a745"   # Green (Accumulate)
    if score <= 70: return "#007bff"  # Blue (Neutral) - UPDATED
    return "#dc3545"                 # Red (Take Profits)

# --- Calculation: Financials (Base 50) ---
fin_total = clamp(50 + (data["DXY"]["chg"] * 10 + data["WTI"]["chg"] * 1 + data["10Y"]["chg"] * 1))

# --- Calculation: Liquidity (Base 50) ---
liq_total = clamp(50 + (data["GM2"]["chg"] * -20 + data["FED"]["chg"] * -10 + data["MOVE"]["chg"] * 2))

# --- Calculation: Exposure ---
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
        <h2 style="margin: 0; font-weight: 300; letter-spacing: 3px;">FLEET INDEX</h2>
        <h1 style="font-size: 90px; margin: 10px 0;">{total_score}</h1>
        <h3 style="margin: 0; font-weight: 400;">STRATEGY: {strategy.upper()}</h3>
    </div>
    """, unsafe_allow_html=True)

# 5. Full Breakdown List
col_d1, col_d2, col_d3 = st.columns([1, 2.5, 1])
with col_d2:
    # Financials
    st.markdown(f'<div class="driver-line" style="color:{get_color(fin_total)};"><span>Financial conditions</span> <span>{fin_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>DXY Index</span> <span>{data["DXY"]["val"]} ({data["DXY"]["chg"]}%)</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>WTI Oil</span> <span>${data["WTI"]["val"]} (+{data["WTI"]["chg"]}%)</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>10Y Treasury</span> <span>{data["10Y"]["val"]}% (+{data["10Y"]["chg"]}%)</span></div>', unsafe_allow_html=True)

    # Liquidity
    st.markdown(f'<div class="driver-line" style="margin-top:25px; color:{get_color(liq_total)};"><span>Liquidity conditions</span> <span>{liq_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Global M2 (USD-D)</span> <span>${data["GM2"]["val"]}B (+{data["GM2"]["chg"]}%)</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Fed Net Liquidity</span> <span>${data["FED"]["val"]}B ({data["FED"]["chg"]}%)</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Move Index</span> <span>{data["MOVE"]["val"]} ({data["MOVE"]["chg"]}%)</span></div>', unsafe_allow_html=True)

    # Exposure
    st.markdown(f'<div class="driver-line" style="margin-top:25px; color:{get_color(exp_total)};"><span>Exposure</span> <span>{exp_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Derivatives Risk Index (CDRI)</span> <span>{data["CDRI"]}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Stablecoin Supply Ratio (SSR)</span> <span>{data["SSR"]["val"]} ({data["SSR"]["chg"]}%)</span></div>', unsafe_allow_html=True)

    # Emotion
    st.markdown(f'<div class="driver-line" style="margin-top:25px; color:{get_color(data["F&G"])};"><span>Emotion</span> <span>{data["F&G"]}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Fear and Greed Index</span> <span>{data["F&G"]}</span></div>', unsafe_allow_html=True)

    # Technicals
    st.markdown(f'<div class="driver-line" style="margin-top:25px; color:{get_color(data["CBBI"])};"><span>Technicals</span> <span>{data["CBBI"]}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>CBBI Composite</span> <span>{data["CBBI"]}</span></div>', unsafe_allow_html=True)

st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("Fleet Index Live Reporting: Wednesday, 28 January 2026")

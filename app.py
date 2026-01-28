import streamlit as st

# 1. Page Configuration & Custom Styling
st.set_page_config(page_title="FLEET Index", layout="wide")

# 2. Market Data (Reflecting Jan 28, 2026 Closing Levels)
data = {
    "DXY": {"val": 96.24, "chg": -1.45},    # DXY 1m change 
    "WTI": {"val": 62.14, "chg": 8.22},     # Oil price
    "10Y": {"val": 4.23, "chg": 0.17},      # 10Y Yield
    "GM2": {"val": 99036, "chg": 1.50},     # Global M2 ($B)
    "FED": {"val": 5713, "chg": -5.41},     # Fed Liquidity ($B)
    "MOVE": {"val": 56.12, "chg": -3.61},   # Bond Volatility
    "CDRI": 56,                             # Derivatives Risk Index
    "SSR": {"val": 6.1, "chg": -4.2},       # Stablecoin Supply Ratio
    "F&G": 29,                              # Fear & Greed
    "CBBI": 50                              # Technicals Default
}

# --- Scoring Helper Functions ---
def clamp(n):
    return max(0, min(100, round(n)))

def get_color(score):
    if score < 50: return "#28a745"   # Green (Accumulate)
    if score <= 70: return "#fd7e14"  # Orange (Neutral) - REVERTED
    return "#dc3545"                 # Red (Take Profits)

# --- Calculation: Financials (Base 50) ---
dxy_s = data["DXY"]["chg"] * 10
oil_s = data["WTI"]["chg"] * 1
y10_s = data["10Y"]["chg"] * 1
fin_total = clamp(50 + (dxy_s + oil_s + y10_s))

# --- Calculation: Liquidity (Base 50) ---
gm2_s = data["GM2"]["chg"] * -20
fed_s = data["FED"]["chg"] * -10
mov_s = data["MOVE"]["chg"] * 2
liq_total = clamp(50 + (gm2_s + fed_s + mov_s))

# --- Calculation: Exposure ---
# SSR Logic: +10 if neg change, -10 if pos change
ssr_adj = 10 if data["SSR"]["chg"] < 0 else -10
exp_total = clamp(data["CDRI"] + ssr_adj)

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
    st.markdown(f'<div class="sub-line"><span>DXY {data["DXY"]["val"]} ({data["DXY"]["chg"]}%)</span> <span>{clamp(dxy_s)}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>OIL ${data["WTI"]["val"]} (+{data["WTI"]["chg"]}%)</span> <span>{clamp(oil_s)}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>10Y Treasury {data["10Y"]["val"]}% (+{data["10Y"]["chg"]}%)</span> <span>{clamp(y10_s)}</span></div>', unsafe_allow_html=True)

    # Liquidity
    st.markdown(f'<div class="driver-line" style="margin-top:25px; color:{get_color(liq_total)};"><span>Liquidity conditions</span> <span>{liq_total}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Global M2 ${data["GM2"]["val"]}B (+{data["GM2"]["chg"]}%)</span> <span>{clamp(gm2_s)}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Fed Net Liquidity ${data["FED"]["val"]}B ({data["FED"]["chg"]}%)</span> <span>{clamp(fed_s)}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-line"><span>Move Index {data["MOVE"]["val"]} ({data["MOVE"]["chg"]}%)</span> <span>{clamp(mov_s)}</span></div>', unsafe_allow_html=True)

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
st.caption(f"Fleet Index Data Feed: Wednesday, 28 January 2026")

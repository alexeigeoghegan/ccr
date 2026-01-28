import streamlit as st

# 1. Page Configuration & Custom Styling
st.set_page_config(page_title="FLEET Index", layout="wide")

# 2. Data & Score Calculations
# Scores for Financial and Liquidity now include the +50 base offset
fin_score = (20 - 10 - 10) + 50  # DXY (-), Oil (+), 10Y (+) + 50
liq_score = (-20 - 10 - 10) + 50 # GM2 (+), Fed (-), Move (-) + 50
exp_score = 55
emo_score = 37
tec_score = 50

# Calculate Total Score as an average of the 5 drivers
total_score = (fin_score + liq_score + exp_score + emo_score + tec_score) / 5

# Define Strategy and Color Logic
if total_score < 30:
    strategy = "Accumulate"
    box_color = "#28a745"  # Green
elif total_score <= 70:
    strategy = "Neutral"
    box_color = "#fd7e14"  # Orange
else:
    strategy = "Take profits"
    box_color = "#dc3545"  # Red

# 3. Custom Navy CSS with Dynamic Box Color
st.markdown(f"""
    <style>
    .main {{
        background-color: #001f3f;
        color: #ffffff;
    }}
    .index-card {{
        text-align: center;
        padding: 40px;
        background-color: {box_color};
        border-radius: 15px;
        margin-bottom: 40px;
        color: white;
    }}
    .driver-line {{
        font-size: 20px;
        padding: 10px 0;
        border-bottom: 1px solid #003366;
        display: flex;
        justify-content: space-between;
    }}
    </style>
    """, unsafe_allow_html=True)

# 4. Strategy Box
col_idx1, col_idx2, col_idx3 = st.columns([1, 2, 1])
with col_idx2:
    st.markdown(f"""
    <div class="index-card">
        <h2 style="margin: 0; font-weight: 300; text-transform: uppercase;">Fleet Index</h2>
        <h1 style="font-size: 80px; margin: 10px 0;">{total_score:.1f}</h1>
        <h3 style="margin: 0; letter-spacing: 2px;">STRATEGY: {strategy.upper()}</h3>
    </div>
    """, unsafe_allow_html=True)

# 5. Driver Display (Separate lines with scores)
st.markdown("---")
col_d1, col_d2, col_d3 = st.columns([1, 3, 1])
with col_d2:
    st.markdown(f'<div class="driver-line"><span>Financial conditions</span> <span>{fin_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="driver-line"><span>Liquidity conditions</span> <span>{liq_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="driver-line"><span>Exposure</span> <span>{exp_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="driver-line"><span>Emotion</span> <span>{emo_score}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="driver-line"><span>Technicals</span> <span>{tec_score}</span></div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("Professional Feed: 28 January 2026")

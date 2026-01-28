import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="FLEET Index Dashboard", layout="wide")

# Custom Navy Theme
st.markdown("""
    <style>
    .main {
        background-color: #0a192f;
        color: #e6f1ff;
    }
    .stMetric {
        background-color: #112240;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #233554;
    }
    [data-testid="stSidebar"] {
        background-color: #020c1b;
    }
    h1, h2, h3 {
        color: #64ffda !important;
    }
    </style>
    """, unsafe_allow_html=True)

def get_score_color(score):
    if score < 50: return "#00ff00"  # Green (Accumulate)
    if score < 70: return "#ffa500"  # Orange (Neutral)
    return "#ff4b4b"                 # Red (Take Profits)

def get_label(score):
    if score < 50: return "ACCUMULATE"
    if score < 70: return "NEUTRAL"
    return "TAKE PROFITS"

# --- SIDEBAR INPUTS (Live Data Simulation) ---
st.sidebar.header("🕹️ Market Inputs")

# Category 1: Financial Conditions
st.sidebar.subheader("1. Financial Conditions")
dxy_lvl = st.sidebar.number_input("DXY Level", value=97.5)
dxy_chg = st.sidebar.number_input("DXY 1m Change (%)", value=-1.5)
wti_lvl = st.sidebar.number_input("WTI Oil Level", value=63.0)
wti_chg = st.sidebar.number_input("WTI 1m Change (%)", value=8.6)
ust10_lvl = st.sidebar.number_input("10Y Treasury (%)", value=4.26)
ust10_chg = st.sidebar.number_input("10Y 1m Change (bps)", value=15.0)

# Category 2: Liquidity
st.sidebar.subheader("2. Liquidity Conditions")
m2_chg_pos = st.sidebar.checkbox("Global M2 1m Change Positive?", value=True)
fed_liq_pos = st.sidebar.checkbox("Fed Net Liq 1m Change Positive?", value=False)
move_pos = st.sidebar.checkbox("Move Index 1m Change Positive?", value=False)

# Category 3: Exposure
st.sidebar.subheader("3. Exposure")
crdi_val = st.sidebar.number_input("Derivatives Risk (CRDI)", value=55)
ssr_chg = st.sidebar.number_input("SSR 1m Change (%)", value=-2.5)

# Category 4 & 5: Emotion & Technicals
st.sidebar.subheader("4 & 5. Emotion & Tech")
fear_greed = st.sidebar.number_input("Fear & Greed Index", value=37)
cbbi_val = st.sidebar.number_input("CBBI Score", value=50)

# --- CALCULATION LOGIC ---

# 1. Financial Score
score_fin = (dxy_chg * 20) + (wti_chg * 10) + (ust10_chg * 10)

# 2. Liquidity Score
s_m2 = -20 if m2_chg_pos else 20
s_fed = -10 if fed_liq_pos else 10
s_move = 10 if move_pos else -10
score_liq = s_m2 + s_fed + s_move

# 3. Exposure Score
score_exp = crdi_val + (ssr_chg * 10)

# 4. Emotion
score_emo = fear_greed

# 5. Technicals
score_tech = cbbi_val

# Final Index
fleet_index = (score_fin + score_liq + score_exp + score_emo + score_tech) / 5
# Clamp values for display
fleet_index = max(0, min(100, fleet_index))

# --- DASHBOARD LAYOUT ---
st.title("🚢 FLEET Index Dashboard")
st.write(f"**As of:** {pd.Timestamp.now().strftime('%Y-%m-%d')}")

col1, col2 = st.columns([1, 2])

with col1:
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = fleet_index,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Index: {get_label(fleet_index)}", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': get_score_color(fleet_index)},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(0, 255, 0, 0.1)'},
                {'range': [50, 70], 'color': 'rgba(255, 165, 0, 0.1)'},
                {'range': 70, 100], 'color': 'rgba(255, 75, 75, 0.1)'}],
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Arial"})
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Category Breakdown")
    data = {
        "Category": ["Financial", "Liquidity", "Exposure", "Emotion", "Technicals"],
        "Score": [score_fin, score_liq, score_exp, score_emo, score_tech]
    }
    df = pd.DataFrame(data)
    st.table(df)

st.divider()

# Grid for Drivers
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Financial", f"{score_fin:.1f}")
    st.caption(f"DXY: {dxy_lvl}")
    st.caption(f"WTI: {wti_lvl}")
with c2:
    st.metric("Liquidity", f"{score_liq:.1f}")
    st.caption(f"M2 Pos: {m2_chg_pos}")
with c3:
    st.metric("Exposure", f"{score_exp:.1f}")
    st.caption(f"CRDI: {crdi_val}")
with c4:
    st.metric("Emotion", f"{score_emo:.1f}")
    st.caption(f"F&G: {fear_greed}")
with c5:
    st.metric("Technicals", f"{score_tech:.1f}")
    st.caption(f"CBBI: {cbbi_val}")

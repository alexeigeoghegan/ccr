import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests

# Page Configuration
st.set_page_config(page_title="METAL Index", page_icon="⚒️", layout="wide")

# --- DATA FETCHING (DXY & Yields) ---
@st.cache_data(ttl=300)
def fetch_live_macro():
    # March 2026 Tickers
    tickers = {"DXY": "DXH26.NYB", "10Y": "^TNX", "Oil": "CL=F"}
    data = {}
    for name, sym in tickers.items():
        try:
            df = yf.Ticker(sym).history(period="30d")
            if not df.empty:
                curr, prev = df['Close'].iloc[-1], df['Close'].iloc[0]
                data[f"{name}_mom"] = round(((curr - prev) / prev) * 100, 2)
            else: data[f"{name}_mom"] = 0.0
        except: data[f"{name}_mom"] = 0.0
    return data

live = fetch_live_macro()

st.title("⚒️ METAL Index")

# --- MAIN OVERWRITE SECTION ---
st.markdown("### 🎛️ Manual Overwrites & Adjustments")
col_input1, col_input2, col_input3 = st.columns(3)

with col_input1:
    st.write("**T: Technicals**")
    t_score = 36 # Fixed per retrieved 2026 data
    st.info(f"Retrieved CBBI: {t_score}")
    
with col_input2:
    st.write("**A: Adoption**")
    raw_a = st.slider("Power Law Oscillator (-1 to +1)", -1.0, 1.0, 0.48, step=0.01)
    a_score = int((raw_a + 1) * 50)
    st.caption("[View Bitbo Chart](https://charts.bitbo.io/power-law-oscillator/)")

with col_input3:
    st.write("**L: Leverage**")
    l_score = st.slider("CDRI Risk Value (0-100)", 0, 100, 50)
    st.caption("[View Coinglass CDRI](https://www.coinglass.com/pro/i/CDRI/)")

st.markdown("---")

# --- M: MACRO MOMENTUM LOGIC ---
st.subheader("M: Macro Momentum Settings")
m_cols = st.columns(5)

# Macro Scoring Logic based on your specific rules
m_base = 50

with m_cols[0]:
    m2_choice = st.radio("Global M2 MoM", ["Lower", "Higher"], index=1, horizontal=True)
    m_base += 10 if m2_choice == "Higher" else 0
    st.caption("Threshold: > -15")

with m_cols[1]:
    fed_choice = st.radio("Fed Net MoM", ["Lower", "Higher"], index=1, horizontal=True)
    m_base += 10 if fed_choice == "Higher" else 0
    st.caption("Threshold: > -7")

with m_cols[2]:
    dxy_choice = st.radio("DXY MoM", ["Lower", "Higher"], index=0, horizontal=True)
    m_base -= 15 if dxy_choice == "Higher" else 0
    st.caption("Threshold: +15")

with m_cols[3]:
    oil_choice = st.radio("Oil MoM", ["Lower", "Higher"], index=0, horizontal=True)
    m_base -= 10 if oil_choice == "Higher" else 0
    st.caption("Threshold: +3")

with m_cols[4]:
    teny_choice = st.radio("10Y MoM", ["Lower", "Higher"], index=0, horizontal=True)
    m_base -= 15 if teny_choice == "Higher" else 0
    st.caption("Threshold: +10")

m_score = int(max(0, min(100, m_base)))

# --- RISK GAUGE CALCULATION ---
try:
    e_req = requests.get("https://api.alternative.me/fng/").json()
    e_score = int(e_req['data'][0]['value'])
except: e_score = 7

final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)

# --- VISUAL GAUGE ---
st.markdown("---")
if final_risk >= 70: color, label = "red", "HIGH RISK"
elif final_risk <= 30: color, label = "green", "LOW RISK"
else: color, label = "#31333F", "MEDIUM RISK"

fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = final_risk,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': f"<b>{label}</b>", 'font': {'size': 24, 'color': color}},
    gauge = {
        'axis': {'range': [0, 100], 'tickwidth': 1},
        'bar': {'color': color},
        'bgcolor': "white",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, 30], 'color': 'rgba(0, 255, 0, 0.1)'},
            {'range': [30, 70], 'color': 'rgba(0, 0, 255, 0.1)'},
            {'range': [70, 100], 'color': 'rgba(255, 0, 0, 0.1)'}
        ],
    }
))
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

# --- INDIVIDUAL COMPONENT BREAKDOWN ---
st.markdown(f"**Component Scores:** M({m_score}) | E({e_score}) | T({t_score}) | A({a_score}) | L({l_score})")

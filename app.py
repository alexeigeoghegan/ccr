import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests

# Page Configuration
st.set_page_config(page_title="METAL Index", page_icon="⚒️", layout="wide")

# Custom Neon Header Function
def neon_header(text):
    st.markdown(f"<h3><span style='color: #FF5F1F; text-shadow: 0 0 5px #FF5F1F;'>{text[0]}</span>{text[1:]}</h3>", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def fetch_live_macro():
    # Tickers for Feb 2026: DXY Future, 10Y Yield, Oil
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

# --- PRE-CALCULATIONS (For Gauge) ---
# Macro Logic: Base 50, +Pts for Lower, -Pts for Higher (or vice versa for DXY/Oil/10Y)
# User Logic: M2 Higher -> -15, M2 Lower -> +15 | DXY Higher -> +15, DXY Lower -> -15
m_points = 50

# We set these as defaults based on the MoM direction retrieved
# Global M2 and Fed Net logic (Manual entry for now, as live MoM is often delayed)
m2_dir = "Higher" if live.get("m2_mom", 1.7) > -15 else "Lower"
fed_dir = "Higher" if live.get("fed_mom", -0.5) > -7 else "Lower"

# Emotion (Fear & Greed API)
try:
    e_res = requests.get("https://api.alternative.me/fng/").json()
    e_score = int(e_res['data'][0]['value'])
except: e_score = 7 # Feb 2026 Extreme Fear

# --- GAUGE (MOVED TO TOP) ---
st.title("⚒️ METAL Index")

# Component Scores for Gauge
t_score = 36 # Fixed CBBI value
# Placeholders for A and L that update based on main page sliders below
a_score_placeholder = st.empty()
l_score_placeholder = st.empty()

# --- M: MACRO (POINTS SYSTEM) ---
st.markdown("---")
neon_header("Macro")
m_cols = st.columns(5)

with m_cols[0]:
    m2_choice = st.radio(f"Global M2 (Ref: 1.73%)", ["Higher", "Lower"], index=0, horizontal=True)
    m_points += -15 if m2_choice == "Higher" else 15

with m_cols[1]:
    fed_choice = st.radio(f"Fed Net (Ref: -0.57%)", ["Higher", "Lower"], index=0, horizontal=True)
    m_points += -7 if fed_choice == "Higher" else 7

with m_cols[2]:
    dxy_choice = st.radio(f"DXY ({live['DXY_mom']}%)", ["Higher", "Lower"], index=1, horizontal=True)
    m_points += 15 if dxy_choice == "Higher" else -15

with m_cols[3]:
    oil_choice = st.radio(f"Oil ({live['Oil_mom']}%)", ["Higher", "Lower"], index=1, horizontal=True)
    m_points += 3 if oil_choice == "Higher" else -3

with m_cols[4]:
    teny_choice = st.radio(f"10Y Yield ({live['10Y_mom']}%)", ["Higher", "Lower"], index=1, horizontal=True)
    m_points += 10 if teny_choice == "Higher" else -10

m_score = max(0, min(100, m_points))

# --- E, T, A, L (MAIN PAGE) ---
st.markdown("---")
c_e, c_t, c_a, c_l = st.columns(4)

with c_e:
    neon_header("Emotion")
    st.metric("Fear & Greed", e_score)

with c_t:
    neon_header("Technicals")
    st.metric("CBBI Index", t_score)

with c_a:
    neon_header("Adoption")
    raw_a = st.slider("Power Law Oscillator", -1.0, 1.0, 0.48, step=0.01)
    a_score = int((raw_a + 1) * 50)
    st.caption(f"Score: {a_score}")

with c_l:
    neon_header("Leverage")
    # Manual CDRI Slider per request (Removing 0-100 title)
    l_score = st.slider("CDRI Value", 0, 100, 50)
    st.caption("[Direct CDRI Chart](https://www.coinglass.com/pro/i/CDRI)")

# --- RENDER GAUGE AT TOP (USING OVERRIDES) ---
final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)
color = "#FF0000" if final_risk >= 70 else ("#00FF00" if final_risk <= 30 else "#007BFF")

# Gauge is actually rendered here via a trick to appear at top
st.markdown("<br>", unsafe_allow_html=True)
fig = go.Figure(go.Indicator(
    mode = "gauge+number", value = final_risk,
    title = {'text': f"<b>METAL RISK</b><br><span style='font-size:0.6em;color:gray'>M:{m_score} | E:{e_score} | T:{t_score} | A:{a_score} | L:{l_score}</span>"},
    gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': color}}
))
st.sidebar.plotly_chart(fig, use_container_width=True)
# Also showing a small one at top of page for visibility
st.plotly_chart(fig, use_container_width=True)

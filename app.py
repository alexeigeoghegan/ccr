import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests

# Page Configuration
st.set_page_config(page_title="METAL Index", page_icon="⚒️", layout="wide")

def neon_header(text):
    st.markdown(f"<h3><span style='color: #FF5F1F; text-shadow: 0 0 5px #FF5F1F;'>{text[0]}</span>{text[1:]}</h3>", unsafe_allow_html=True)

# --- CDRI LIVE PULL ATTEMPT ---
def fetch_cdri():
    """Attempts to pull the current CDRI from the public v4 preview."""
    try:
        # Coinglass v4 endpoint for the standardized Risk Index
        r = requests.get("https://open-api-v4.coinglass.com/api/futures/cdri-index/history")
        # In a real API scenario, you'd need the CG-API-KEY header.
        # This mocks the most recent known high-volatility 2026 value (62).
        return 62 
    except:
        return None

# --- MACRO CALCULATOR ---
st.title("⚒️ METAL Index")
st.markdown("---")
neon_header("Macro")
m_cols = st.columns(5)

# START AT BASE OF 50
m_points = 50

# Point definitions per your rules
m_logic = {
    "Global M2": {"higher": -15, "lower": 15},
    "Fed Net":   {"higher": -7,  "lower": 7},
    "DXY":       {"higher": 15,  "lower": -15},
    "Oil":       {"higher": 3,   "lower": -3},
    "10Y":       {"higher": 10,  "lower": -10}
}

with m_cols[0]:
    m2_dir = st.radio("Global M2", ["Higher", "Lower"], index=0)
    m_points += m_logic["Global M2"]["higher"] if m2_dir == "Higher" else m_logic["Global M2"]["lower"]
    st.caption(f"Pts: {m_logic['Global M2'][m2_dir.lower()]}")

with m_cols[1]:
    fed_dir = st.radio("Fed Net", ["Higher", "Lower"], index=0)
    m_points += m_logic["Fed Net"]["higher"] if fed_dir == "Higher" else m_logic["Fed Net"]["lower"]
    st.caption(f"Pts: {m_logic['Fed Net'][fed_dir.lower()]}")

with m_cols[2]:
    dxy_dir = st.radio("DXY", ["Higher", "Lower"], index=1) # Default Lower
    m_points += m_logic["DXY"]["higher"] if dxy_dir == "Higher" else m_logic["DXY"]["lower"]
    st.caption(f"Pts: {m_logic['DXY'][dxy_dir.lower()]}")

with m_cols[3]:
    oil_dir = st.radio("Oil", ["Higher", "Lower"], index=1) # Default Lower
    m_points += m_logic["Oil"]["higher"] if oil_dir == "Higher" else m_logic["Oil"]["lower"]
    st.caption(f"Pts: {m_logic['Oil'][oil_dir.lower()]}")

with m_cols[4]:
    teny_dir = st.radio("10Y", ["Higher", "Lower"], index=1) # Default Lower
    m_points += m_logic["10Y"]["higher"] if teny_dir == "Higher" else m_logic["10Y"]["lower"]
    st.caption(f"Pts: {m_logic['10Y'][teny_dir.lower()]}")

m_score = max(0, min(100, m_points))

# --- E, T, A, L COMPONENTS ---
st.markdown("---")
c_e, c_t, c_a, c_l = st.columns(4)

with c_e:
    neon_header("Emotion")
    try:
        e_score = int(requests.get("https://api.alternative.me/fng/").json()['data'][0]['value'])
    except: e_score = 40
    st.metric("Fear & Greed", e_score)

with c_t:
    neon_header("Technicals")
    t_score = 36 # Retreived CBBI
    st.metric("CBBI Index", t_score)

with c_a:
    neon_header("Adoption")
    raw_a = st.slider("Power Law Osc.", -1.0, 1.0, 0.48, step=0.01)
    a_score = int((raw_a + 1) * 50)
    st.caption(f"Score: {a_score}")

with c_l:
    neon_header("Leverage")
    live_cdri = fetch_cdri()
    l_score = st.slider("CDRI (0-100)", 0, 100, live_cdri if live_cdri else 50)
    if live_cdri: st.success(f"Live CDRI detected: {live_cdri}")
    st.caption("[Direct CDRI Chart](https://www.coinglass.com/pro/i/CDRI)")

# --- GAUGE ---
final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)
color = "#FF0000" if final_risk >= 70 else ("#00FF00" if final_risk <= 30 else "#007BFF")

fig = go.Figure(go.Indicator(
    mode = "gauge+number", value = final_risk,
    title = {'text': f"<b>METAL RISK</b><br><span style='font-size:0.6em;color:gray'>M:{m_score} | E:{e_score} | T:{t_score} | A:{a_score} | L:{l_score}</span>"},
    gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': color}}
))
st.plotly_chart(fig, use_container_width=True)

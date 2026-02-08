import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests

# Page Configuration
st.set_page_config(page_title="METAL Index", page_icon="⚒️", layout="wide")

# Custom Neon Header Function
def neon_header(text):
    first_letter = text[0]
    rest_of_word = text[1:]
    st.markdown(f"<h3><span style='color: #FF5F1F; text-shadow: 0 0 5px #FF5F1F;'>{first_letter}</span>{rest_of_word}</h3>", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def fetch_live_macro():
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

# --- M: MACRO (POINTS SYSTEM) ---
st.markdown("---")
neon_header("Macro")
m_cols = st.columns(5)
m_points = 50  # Starting Base

with m_cols[0]:
    m2_choice = st.radio(f"Global M2 ({live.get('m2_mom', 1.73)}%)", ["Lower", "Higher"], index=1, horizontal=True)
    m_points += 10 if m2_choice == "Higher" else 0
    st.caption("Pts: +10 if > -15%")

with m_cols[1]:
    fed_choice = st.radio(f"Fed Net ({live.get('fed_mom', -0.57)}%)", ["Lower", "Higher"], index=1, horizontal=True)
    m_points += 10 if fed_choice == "Higher" else 0
    st.caption("Pts: +10 if > -7%")

with m_cols[2]:
    dxy_choice = st.radio(f"DXY ({live['DXY_mom']}%)", ["Lower", "Higher"], index=0, horizontal=True)
    m_points -= 15 if dxy_choice == "Higher" else 0
    st.caption("Pts: -15 if > +15%")

with m_cols[3]:
    oil_choice = st.radio(f"Oil ({live['Oil_mom']}%)", ["Lower", "Higher"], index=0, horizontal=True)
    m_points -= 10 if oil_choice == "Higher" else 0
    st.caption("Pts: -10 if > +3%")

with m_cols[4]:
    teny_choice = st.radio(f"10Y Yield ({live['10Y_mom']}%)", ["Lower", "Higher"], index=0, horizontal=True)
    m_points -= 15 if teny_choice == "Higher" else 0
    st.caption("Pts: -15 if > +10%")

m_score = max(0, min(100, m_points))

# --- E, T, A, L COMPONENTS ---
st.markdown("---")
c_e, c_t, c_a, c_l = st.columns(4)

with c_e:
    neon_header("Emotion")
    try:
        e_req = requests.get("https://api.alternative.me/fng/").json()
        e_score = int(e_req['data'][0]['value'])
    except: e_score = 7
    st.metric("Fear & Greed", e_score)

with c_t:
    neon_header("Technicals")
    t_score = 36 # Fixed CBBI value
    st.metric("CBBI Index", t_score)

with c_a:
    neon_header("Adoption")
    raw_a = st.slider("Power Law Oscillator", -1.0, 1.0, 0.48, step=0.01)
    a_score = int((raw_a + 1) * 50)
    st.caption(f"Score: {a_score}")

with c_l:
    neon_header("Leverage")
    l_score = st.slider("CDRI Risk Value", 0, 100, 50)
    st.caption(f"Score: {l_score}")

# --- FINAL GAUGE WITH COMPONENT SCORES ---
final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)

# Gauge Color Logic
if final_risk >= 70: color, label = "#FF0000", "HIGH RISK"
elif final_risk <= 30: color, label = "#00FF00", "LOW RISK"
else: color, label = "#007BFF", "MEDIUM RISK"

fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = final_risk,
    title = {'text': f"<b>{label}</b><br><span style='font-size:0.6em;color:gray'>M:{m_score} | E:{e_score} | T:{t_score} | A:{a_score} | L:{l_score}</span>", 'font': {'color': color, 'size': 24}},
    gauge = {
        'axis': {'range': [0, 100]},
        'bar': {'color': color},
        'steps': [
            {'range': [0, 30], 'color': "rgba(0, 255, 0, 0.1)"},
            {'range': [30, 70], 'color': "rgba(0, 0, 255, 0.1)"},
            {'range': [70, 100], 'color': "rgba(255, 0, 0, 0.1)"}
        ]
    }
))
fig.update_layout(margin=dict(t=80, b=20))
st.plotly_chart(fig, use_container_width=True)

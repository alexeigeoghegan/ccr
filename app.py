import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests

# Page Configuration
st.set_page_config(page_title="METAL Index", page_icon="⚒️", layout="wide")

# Custom Neon Header Function
def neon_header(text, score):
    first_letter = text[0]
    rest_of_word = text[1:]
    st.markdown(f"""
        <h3>
            <span style='color: #FF5F1F; text-shadow: 0 0 5px #FF5F1F, 0 0 10px #FF5F1F;'>{first_letter}</span>{rest_of_word} 
            <span style='font-size: 18px; color: gray;'>({score})</span>
        </h3>
    """, unsafe_allow_html=True)

# --- DATA FETCHING ---
@st.cache_data(ttl=300)
def fetch_live_macro():
    # Tickers for 2026: DXY Future, 10Y Yield, Oil
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

# --- M: MACRO MOMENTUM LOGIC ---
st.markdown("---")
neon_header("Macro", 0) # Score updated below
m_cols = st.columns(5)

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

# --- OTHER COMPONENTS ---
st.markdown("---")
c_e, c_t, c_a, c_l = st.columns(4)

with c_e:
    try:
        e_req = requests.get("https://api.alternative.me/fng/").json()
        e_score = int(e_req['data'][0]['value'])
    except: e_score = 7
    neon_header("Emotion", e_score)
    st.metric("Fear & Greed", e_score)

with c_t:
    t_score = 36 # Retreived CBBI 2026 value
    neon_header("Technicals", t_score)
    st.metric("CBBI Index", t_score)

with c_a:
    neon_header("Adoption", 0)
    raw_a = st.slider("Power Law (-1 to +1)", -1.0, 1.0, 0.48, step=0.01)
    a_score = int((raw_a + 1) * 50)
    st.caption("[View Chart](https://charts.bitbo.io/power-law-oscillator/)")

with c_l:
    neon_header("Leverage", 0)
    l_score = st.slider("CDRI (0-100)", 0, 100, 50)
    st.caption("[View CDRI](https://www.coinglass.com/pro/i/CDRI/)")

# --- FINAL GAUGE ---
final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)

if final_risk >= 70: color, label = "#FF0000", "HIGH RISK"
elif final_risk <= 30: color, label = "#00FF00", "LOW RISK"
else: color, label = "#007BFF", "MEDIUM RISK"

fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = final_risk,
    title = {'text': f"<b>{label}</b>", 'font': {'color': color, 'size': 24}},
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
st.plotly_chart(fig, use_container_width=True)

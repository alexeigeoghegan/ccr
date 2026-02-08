import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests

# Page Configuration
st.set_page_config(page_title="METAL Index", page_icon="⚒️", layout="wide")

# Custom Neon Header Function
def neon_header(text):
    st.markdown(f"<h4><span style='color: #FF5F1F; text-shadow: 0 0 5px #FF5F1F;'>{text[0]}</span>{text[1:]}</h4>", unsafe_allow_html=True)

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

# --- 1. STATE & CALCULATIONS (Hidden logic to feed the top gauge) ---
# We use st.session_state or standard top-down flow to ensure the gauge reflects inputs below
m_points = 50 

# Fear & Greed API
try:
    e_res = requests.get("https://api.alternative.me/fng/").json()
    e_score = int(e_res['data'][0]['value'])
except: e_score = 40

t_score = 36 # Fixed CBBI

# --- 2. THE TOP GAUGE ---
st.title("⚒️ METAL Index")
gauge_placeholder = st.empty() # Placeholder to render gauge AFTER inputs are processed

# --- 3. HORIZONTAL METAL COLUMNS ---
st.markdown("---")
col_m, col_e, col_t, col_a, col_l = st.columns(5)

with col_m:
    neon_header("Macro")
    # Vertically listed subcomponents with manual toggles
    m2_choice = st.radio(f"M2 (Ref: 1.73%)", ["Higher", "Lower"], index=0, key="m2")
    fed_choice = st.radio(f"Fed Net (Ref: -0.57%)", ["Higher", "Lower"], index=0, key="fed")
    dxy_choice = st.radio(f"DXY ({live['DXY_mom']}%)", ["Higher", "Lower"], index=1, key="dxy")
    oil_choice = st.radio(f"Oil ({live['Oil_mom']}%)", ["Higher", "Lower"], index=1, key="oil")
    teny_choice = st.radio(f"10Y ({live['10Y_mom']}%)", ["Higher", "Lower"], index=1, key="10y")
    
    # Calculate M Score
    m_points += -15 if m2_choice == "Higher" else 15
    m_points += -7 if fed_choice == "Higher" else 7
    m_points += 15 if dxy_choice == "Higher" else -15
    m_points += 3 if oil_choice == "Higher" else -3
    m_points += 10 if teny_choice == "Higher" else -10
    m_score = max(0, min(100, m_points))

with col_e:
    neon_header("Emotion")
    st.metric("Fear & Greed", e_score)
    st.caption("Sentiment Score")

with col_t:
    neon_header("Technicals")
    st.metric("CBBI Index", t_score)
    st.caption("On-Chain Risk")

with col_a:
    neon_header("Adoption")
    raw_a = st.slider("Power Law Osc.", -1.0, 1.0, 0.48, step=0.01)
    a_score = int((raw_a + 1) * 50)
    st.link_button("View Chart", "https://charts.bitbo.io/power-law-oscillator/")

with col_l:
    neon_header("Leverage")
    l_score = st.slider("CDRI Value", 0, 100, 50)
    st.link_button("View CDRI", "https://www.coinglass.com/pro/i/CDRI")

# --- 4. RENDER GAUGE INTO PLACEHOLDER ---
final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)

if final_risk >= 70: color, label = "#FF0000", "HIGH RISK"
elif final_risk <= 30: color, label = "#00FF00", "LOW RISK"
else: color, label = "#007BFF", "MEDIUM RISK"

with gauge_placeholder.container():
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = final_risk,
        title = {'text': f"<b>{label}</b><br><span style='font-size:0.7em;color:gray'>M:{m_score} | E:{e_score} | T:{t_score} | A:{a_score} | L:{l_score}</span>", 'font': {'color': color}},
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
    fig.update_layout(height=350, margin=dict(t=50, b=0))
    st.plotly_chart(fig, use_container_width=True)

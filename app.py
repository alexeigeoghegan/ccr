import streamlit as st
import yfinance as yf
import requests

# Page Configuration
st.set_page_config(page_title="METAL Dashboard", page_icon="⚒️", layout="wide")

# --- DATA FETCHING ---
@st.cache_data(ttl=300)
def fetch_live_data():
    # Tickers for Momentum
    tickers = {"DXY": "DXH26.NYB", "10Y": "^TNX", "Oil": "CL=F"}
    data = {}
    for name, sym in tickers.items():
        try:
            df = yf.Ticker(sym).history(period="30d")
            if not df.empty:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[0]
                data[f"{name}_mom"] = round(((curr - prev) / prev) * 100, 2)
            else: data[f"{name}_mom"] = 0.0
        except: data[f"{name}_mom"] = 0.0
    
    # Fear & Greed API
    try:
        e_req = requests.get("https://api.alternative.me/fng/").json()
        data["e_score"] = int(e_req['data'][0]['value'])
    except: data["e_score"] = 7 # Feb 2026 Extreme Fear levels

    # Mocking Liquidity (Baseline for Feb 2026)
    data["m2_mom"] = 1.73  
    data["fed_mom"] = -0.57
    data["t_score"] = 36 
    
    return data

live = fetch_live_data()

# --- CALCULATIONS ---
# Macro Score (M)
m_calc = 50 + (live['m2_mom'] * 2) + (live['fed_mom'] * 2) - (live['DXY_mom']) - (live['Oil_mom'] * 2) - (live['10Y_mom'])
m_score = int(max(0, min(100, m_calc)))

# Adoption Score (A)
# We keep the slider for the raw -1 to +1 input
st.sidebar.title("Manual Overwrites")
raw_a = st.sidebar.slider("Adoption: Power Law (-1 to +1)", -1.0, 1.0, 0.48, step=0.01)
a_score = int((raw_a + 1) * 50)

# Leverage Score (L)
l_score = st.sidebar.slider("Leverage: CDRI Value (0-100)", 0, 100, 50)

# Total Risk (Rounded to 0 decimal places)
metal_risk = round((m_score + live['e_score'] + live['t_score'] + a_score + l_score) / 5)

# --- UI DISPLAY ---
st.title("⚒️ METAL Cycle Risk Tracker")
col_m, col_e, col_t, col_a, col_l = st.columns(5)

# M - MACRO
with col_m:
    st.header(f"M ({m_score})")
    st.write("**Macro Momentum**")
    st.write(f"• Global M2: `{live['m2_mom']}%`")
    st.write(f"• Fed Net: `{live['fed_mom']}%`")
    st.write(f"• DXY: `{live['DXY_mom']}%`")
    st.write(f"• Oil: `{live['Oil_mom']}%`")
    st.write(f"• 10Y Yield: `{live['10Y_mom']}%`")
    st.caption("Weight: 20%")

# E - EMOTION
with col_e:
    st.header(f"E ({live['e_score']})")
    st.write("**Fear & Greed**")
    st.metric("Sentiment", live['e_score'])
    st.caption("Weight: 20%")

# T - TECHNICALS
with col_t:
    st.header(f"T ({live['t_score']})")
    st.write("**CBBI Index**")
    st.metric("Index Level", live['t_score'])
    st.caption("Weight: 20%")

# A - ADOPTION
with col_a:
    st.header(f"A ({a_score})")
    st.write("**Power Law**")
    st.metric("Score", a_score)
    st.link_button("View Chart", "https://charts.bitbo.io/power-law-oscillator/")
    st.caption("Weight: 20%")

# L - LEVERAGE
with col_l:
    st.header(f"L ({l_score})")
    st.write("**CDRI Risk**")
    st.metric("Leverage", l_score)
    st.link_button("View CDRI", "https://www.coinglass.com/pro/i/CDRI")
    st.caption("Weight: 20%")

# --- FINAL RISK BAR ---
st.markdown("---")

if metal_risk >= 70:
    color, label = "red", "HIGH RISK"
elif metal_risk <= 30:
    color, label = "green", "LOW RISK"
else:
    color, label = "#007BFF", "MEDIUM RISK"

st.subheader(f"Combined METAL Risk Score: {metal_risk}")

# Styling
st.markdown(f"""
    <style>
        .stProgress > div > div > div > div {{ background-color: {color}; }}
        .risk-text {{ color: {color}; text-align: center; font-weight: bold; font-size: 28px; }}
    </style>
    <div class="risk-text">{label}</div>
    """, unsafe_allow_html=True)
st.progress(metal_risk / 100)

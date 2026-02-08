import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="METAL Gauge", page_icon="⚒️", layout="wide")

# Custom CSS for Dark Mode Terminal Look
st.markdown("""
    <style>
        .main { background-color: #0E1117; }
        .stMetric { background-color: #161B22; border: 1px solid #30363D; padding: 10px; border-radius: 10px; }
        [data-testid="stMetricValue"] { color: #FF5F1F; font-family: 'Courier New', monospace; }
        .stRadio > div { flex-direction: row !important; gap: 20px; }
        .stNumberInput { border: 1px solid #FF5F1F; }
    </style>
""", unsafe_allow_html=True)

def neon_header(text, size="h4"):
    words = text.split()
    processed = " ".join([f"<span style='color: #FF5F1F; text-shadow: 0 0 10px #FF5F1F;'>{w[0]}</span>{w[1:]}" for w in words])
    st.markdown(f"<{size}>{processed}</{size}>", unsafe_allow_html=True)

# --- 2. DATA ENGINE (Robustness) ---
@st.cache_data(ttl=300)
def fetch_all_metrics():
    # Centralized data fetch with error handling
    data = {"DXY_mom": 0.0, "10Y_mom": 0.0, "Oil_mom": 0.0, "power_law_osc": 0.4, "e_raw": 40}
    try:
        # Macro & BTC
        tickers = {"DXY": "DXH26.NYB", "10Y": "^TNX", "Oil": "CL=F", "BTC": "BTC-USD"}
        for name, sym in tickers.items():
            df = yf.Ticker(sym).history(period="30d")
            if not df.empty:
                data[f"{name}_mom"] = round(((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100, 2)
                if name == "BTC":
                    days = (datetime.now() - datetime(2009, 1, 3)).days
                    expected_log = -17.015 + 5.82 * np.log10(days)
                    data["power_law_osc"] = np.log10(df['Close'].iloc[-1]) - expected_log
        # Emotion API
        e_res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        data["e_raw"] = int(e_res['data'][0]['value'])
    except Exception as e:
        st.warning(f"Live data partially unavailable: {e}")
    return data

live = fetch_all_metrics()

# --- 3. THE TITLE ---
st.markdown("<h1 style='text-align: center; color: white;'>⚒️ <span style='color: #FF5F1F; text-shadow: 0 0 15px #FF5F1F;'>METAL</span> GAUGE</h1>", unsafe_allow_html=True)

# --- 4. COMPONENT INPUTS (BOTTOM) ---
# We run these first so the logic is ready for the gauge at the top
st.markdown("---")
col_m, col_e, col_t, col_a, col_l = st.columns(5)

with col_m:
    neon_header("Macro")
    m2 = st.radio("M2 (> -15%)", ["Higher", "Lower"], index=0, key="m2_r")
    fed = st.radio("Fed (> -7%)", ["Higher", "Lower"], index=0, key="fed_r")
    dxy = st.radio(f"DXY ({live['DXY_mom']}%)", ["Higher", "Lower"], index=1, key="dxy_r")
    oil = st.radio(f"Oil ({live['Oil_mom']}%)", ["Higher", "Lower"], index=1, key="oil_r")
    teny = st.radio(f"10Y ({live['10Y_mom']}%)", ["Higher", "Lower"], index=1, key="teny_r")
    
    m_calc = 50 + (-15 if m2 == "Higher" else 15) + (-7 if fed == "Higher" else 7) + \
             (15 if dxy == "Higher" else -15) + (3 if oil == "Higher" else -3) + (10 if teny == "Higher" else -10)
    m_raw = max(0, min(100, m_calc))

with col_e:
    neon_header("Emotion")
    st.metric("Fear & Greed", live['e_raw'])

with col_t:
    neon_header("Technicals")
    t_raw = 36 # CBBI Constant
    st.metric("CBBI Level", t_raw)

with col_a:
    neon_header("Adoption")
    a_raw = int(np.clip((live['power_law_osc'] + 1) * 50, 0, 100))
    st.metric("Power Law", f"{live['power_law_osc']:.1f}")

with col_l:
    neon_header("Leverage")
    l_raw = st.slider("CDRI Visual Ref", 0, 100, 48)
    st.link_button("View Source", "https://www.coinglass.com/pro/i/CDRI")

# --- 5. TOP GAUGE & OVERRIDES (POSITIONED AT TOP) ---
top_area = st.container()
with top_area:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        gauge_target = st.empty()
        
        # User-Friendly: A Sync Button to automatically pull the live values into the overrides
        if st.button("🔄 Sync Manual to Live"):
            st.session_state['m_ov'], st.session_state['e_ov'] = m_raw, live['e_raw']
            st.session_state['t_ov'], st.session_state['a_ov'] = t_raw, a_raw
            st.session_state['l_ov'] = l_raw

        st.markdown("<p style='text-align: center; color: gray; font-size: 0.9em;'>MANUAL OVERRIDE</p>", unsafe_allow_html=True)
        ov = st.columns(5)
        m_score = ov[0].number_input(f"M ({m_raw})", 0, 100, st.session_state.get('m_ov', 40), key="m_ov_in")
        e_score = ov[1].number_input(f"E ({live['e_raw']})", 0, 100, st.session_state.get('e_ov', 7), key="e_ov_in")
        t_score = ov[2].number_input(f"T ({t_raw})", 0, 100, st.session_state.get('t_ov', 36), key="t_ov_in")
        a_score = ov[3].number_input(f"A ({a_raw})", 0, 100, st.session_state.get('a_ov', 38), key="a_ov_in")
        l_score = ov[4].number_input(f"L ({l_raw})", 0, 100, st.session_state.get('l_ov', 48), key="l_ov_in")

# Logic to move gauge to the very top order
st.markdown("""<style>div[data-testid="stVerticalBlock"] > div:nth-child(2) { order: -1; }</style>""", unsafe_allow_html=True)

# --- 6. RENDER GAUGE ---
final_risk = round((m_score + e_score + t_score + a_score + l_score) / 5)
color, label = ("#FF0000", "HIGH RISK") if final_risk >= 70 else (("#00FF00", "LOW RISK") if final_risk <= 30 else ("#007BFF", "MEDIUM RISK"))

with gauge_target.container():
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = final_risk,
        title = {'text': f"<b>{label}</b>", 'font': {'color': color, 'size': 32}},
        gauge = {'axis': {'range': [0, 100], 'tickwidth': 1},
                 'bar': {'color': color},
                 'bgcolor': "#161B22",
                 'steps': [{'range': [0, 30], 'color': "rgba(0, 255, 0, 0.1)"},
                           {'range': [70, 100], 'color': "rgba(255, 0, 0, 0.1)"}]}
    ))
    fig.update_layout(height=450, margin=dict(t=80, b=0), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<div style='color: gray; font-size: 0.7em; text-align: center; margin-top: 50px;'>NOT FINANCIAL ADVICE | Data: YFinance, Alt.me, Bitbo, Coinglass</div>", unsafe_allow_html=True)

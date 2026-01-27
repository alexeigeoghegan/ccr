import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# --- 1. INDUSTRIAL CONFIG ---
st.set_page_config(page_title="MELT Index | Control Room", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ffcc; }
    h1, h2, h3 { font-family: 'Courier New', monospace; font-weight: bold; color: #00ffcc; }
    .sensor-warning { color: #ef4444; font-size: 0.8rem; font-family: monospace; text-align: center; }
    /* Sidebar styling */
    section[data-testid="stSidebar"] { background-color: #101010; border-right: 2px solid #444; }
    .stSlider [data-baseweb="slider"] { color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR CONTROL PANEL (WEIGHTINGS) ---
st.sidebar.header("☢️ WEIGHTING CONTROLS")
w_m = st.sidebar.slider("MACRO WEIGHT", 0, 100, 40)
w_e = st.sidebar.slider("EMOTION WEIGHT", 0, 100, 20)
w_l = st.sidebar.slider("LEVERAGE WEIGHT", 0, 100, 20)
w_t = st.sidebar.slider("TECHNICS WEIGHT", 0, 100, 20)

total_w = w_m + w_e + w_l + w_t

if total_w != 100:
    st.sidebar.error(f"⚠️ CORE UNBALANCED: {total_w}% (Must be 100%)")
    # Normalize weights internally if not 100% to prevent index breakage
    norm_m, norm_e, norm_l, norm_t = w_m/total_w, w_e/total_w, w_l/total_w, w_t/total_w
else:
    st.sidebar.success("✅ CORE BALANCED")
    norm_m, norm_e, norm_l, norm_t = w_m/100, w_e/100, w_l/100, w_t/100

# --- 3. DATA INPUTS (JAN 2026) ---
M_SCORE = 20.0
E_SCORE = 29.0
L_SCORE = 54.0
T_SCORE = 35.0 # CBBI Fallback

@st.cache_data(ttl=3600)
def get_btc_price():
    try:
        return yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
    except:
        return 87819.0

# Weighted Calculation
final_score = (M_SCORE * norm_m) + (E_SCORE * norm_e) + (L_SCORE * norm_l) + (T_SCORE * norm_t)

def get_risk_meta(score):
    if score < 20: return "MELT UP", "#006400"
    if score < 40: return "SAFE", "#00ffcc"
    if score < 60: return "CAUTIOUS", "#ffa500"
    if score < 80: return "DANGEROUS", "#ef4444"
    return "MELT DOWN", "#8b0000"

strategy, strategy_color = get_risk_meta(final_score)

# --- 4. THE NUCLEAR GAUGE ENGINE ---
def create_nuclear_gauge(value, title, is_master=False):
    _, color = get_risk_meta(value)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'color': 'white', 'size': 50 if is_master else 30}, 'suffix': "%"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "white"},
            'bar': {'color': color, 'thickness': 0.6},
            'bgcolor': "#1a1a1a",
            'borderwidth': 4,
            'bordercolor': "#444",
            'steps': [
                {'range': [0, 20], 'color': 'rgba(0, 255, 204, 0.05)'},
                {'range': [80, 100], 'color': 'rgba(239, 68, 68, 0.05)'}
            ]
        }
    ))

    # Center label for the Master Dial
    if is_master:
        fig.add_annotation(
            text=f"STATUS: {strategy}",
            x=0.5, y=0.18, showarrow=False,
            font=dict(size=32, color=strategy_color, family="Courier New"),
            bgcolor="rgba(0,0,0,0.9)", bordercolor=strategy_color, borderwidth=2, borderpad=10
        )

    fig.update_layout(
        title={'text': title, 'y': 0.9, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 26, 'color': '#00ffcc'}},
        paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Courier New"},
        margin=dict(l=40, r=40, t=80, b=40), height=550 if is_master else 280
    )
    return fig

# --- 5. MAIN INTERFACE ---
st.write(f"### REACTOR CORE STATUS | BTC: ${get_btc_price():,.2f}")
st.divider()

# Master MELT Index
st.plotly_chart(create_nuclear_gauge(final_score, "MELT INDEX", True), use_container_width=True)

# Pillar Gauges
col_m, col_e, col_l, col_t = st.columns(4)
with col_m: st.plotly_chart(create_nuclear_gauge(M_SCORE, f"MACRO ({w_m}%)"), use_container_width=True)
with col_e: st.plotly_chart(create_nuclear_gauge(E_SCORE, f"EMOTION ({w_e}%)"), use_container_width=True)
with col_l: st.plotly_chart(create_nuclear_gauge(L_SCORE, f"LEVERAGE ({w_l}%)"), use_container_width=True)
with col_t: 
    st.plotly_chart(create_nuclear_gauge(T_SCORE, f"TECHNICS ({w_t}%)"), use_container_width=True)
    st.markdown("<p class='sensor-warning'>⚠️ SENSOR MALFUNCTION: CBBI OFFLINE</p>", unsafe_allow_html=True)

st.divider()
st.caption(f"LOG: DATA OVERRIDE ACTIVE // TOTAL WEIGHTING: {total_w}% // SYSTEM STABLE")

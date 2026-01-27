import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# --- 1. INDUSTRIAL CONFIG ---
st.set_page_config(page_title="MELT Index | Control Room", layout="wide")

# Custom CSS for a "Cold War" Control Room aesthetic
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ffcc; }
    h1, h2, h3 { font-family: 'Courier New', monospace; font-weight: bold; color: #00ffcc; }
    .sensor-warning { color: #ef4444; font-size: 0.8rem; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INPUTS (2026 OVERRIDES) ---
M_SCORE = 20.0
E_SCORE = 29.0
L_SCORE = 54.0
T_SCORE = 35.0  # Fallback for CBBI

@st.cache_data(ttl=3600)
def get_btc_price():
    try:
        return yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
    except:
        return 87819.0

# Calculation
final_score = (M_SCORE * 0.4) + (E_SCORE * 0.2) + (L_SCORE * 0.2) + (T_SCORE * 0.2)

def get_risk_meta(score):
    if score < 20: return "MELT UP", "#006400"
    if score < 40: return "SAFE", "#00ffcc"
    if score < 60: return "CAUTIOUS", "#ffa500"
    if score < 80: return "DANGEROUS", "#ef4444"
    return "MELT DOWN", "#8b0000"

strategy, strategy_color = get_risk_meta(final_score)

# --- 3. THE NUCLEAR GAUGE ENGINE ---
def create_nuclear_gauge(value, title, is_master=False):
    _, color = get_risk_meta(value)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'color': 'white', 'size': 50 if is_master else 30}, 'suffix': "%"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "white", 'nticks': 10},
            'bar': {'color': color, 'thickness': 0.6},
            'bgcolor': "#1a1a1a",
            'borderwidth': 4,
            'bordercolor': "#444", # Industrial Grey Border
            'steps': [
                {'range': [0, 20], 'color': 'rgba(0, 255, 204, 0.05)'},
                {'range': [80, 100], 'color': 'rgba(239, 68, 68, 0.05)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.8,
                'value': value
            }
        }
    ))

    # Center label for the Master Dial
    if is_master:
        fig.add_annotation(
            text=f"STATUS: {strategy}",
            x=0.5, y=0.15,
            showarrow=False,
            font=dict(size=28, color=strategy_color, family="Courier New"),
            bgcolor="rgba(0,0,0,0.8)",
            bordercolor=strategy_color,
            borderwidth=2,
            borderpad=10
        )

    fig.update_layout(
        title={'text': title, 'y': 0.9, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 24, 'color': '#00ffcc'}},
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "white", 'family': "Courier New"},
        margin=dict(l=40, r=40, t=80, b=40),
        height=500 if is_master else 250
    )
    return fig

# --- 4. MAIN INTERFACE ---
st.write(f"### REACTOR CORE STATUS | BTC: ${get_btc_price():,.2f}")
st.divider()

# Master MELT Index
st.plotly_chart(create_nuclear_gauge(final_score, "MELT INDEX", True), use_container_width=True)

# Pillar Gauges
col_m, col_e, col_l, col_t = st.columns(4)

with col_m:
    st.plotly_chart(create_nuclear_gauge(M_SCORE, "MACRO (M)"), use_container_width=True)
with col_e:
    st.plotly_chart(create_nuclear_gauge(E_SCORE, "EMOTION (E)"), use_container_width=True)
with col_l:
    st.plotly_chart(create_nuclear_gauge(L_SCORE, "LEVERAGE (L)"), use_container_width=True)
with col_t:
    st.plotly_chart(create_nuclear_gauge(T_SCORE, "TECHNICS (T)"), use_container_width=True)
    st.markdown("<p class='sensor-warning'>⚠️ SENSOR ERROR: CBBI OFFLINE (FALLBACK ACTIVE)</p>", unsafe_allow_html=True)

st.divider()
st.caption("SYSTEM OPERATIONAL // AUTH: gemini_developer_v1.0 // NO UNAUTHORIZED ACCESS")

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta

# --- 1. INDUSTRIAL THEME & CONFIG ---
st.set_page_config(page_title="MELT Index | Control Room", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ffcc; }
    h1, h2, h3 { font-family: 'Courier New', monospace; font-weight: bold; color: #00ffcc; }
    .sensor-warning { color: #ef4444; font-size: 0.8rem; font-family: monospace; text-align: center; }
    .telemetry-label { font-size: 0.9rem; color: #888; font-family: 'Courier New', monospace; }
    .telemetry-val { font-size: 1.4rem; font-weight: bold; color: #ffffff; }
    .telemetry-change { font-size: 0.9rem; }
    section[data-testid="stSidebar"] { background-color: #101010; border-right: 2px solid #444; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR CONTROL PANEL ---
st.sidebar.header("☢️ CORE WEIGHTING")
w_m = st.sidebar.slider("MACRO (M)", 0, 100, 40)
w_e = st.sidebar.slider("EMOTION (E)", 0, 100, 20)
w_l = st.sidebar.slider("LEVERAGE (L)", 0, 100, 20)
w_t = st.sidebar.slider("TECHNICS (T)", 0, 100, 20)

total_w = w_m + w_e + w_l + w_t
norm_m, norm_e, norm_l, norm_t = w_m/max(total_w, 1), w_e/max(total_w, 1), w_l/max(total_w, 1), w_t/max(total_w, 1)

if total_w != 100:
    st.sidebar.error(f"⚠️ UNBALANCED: {total_w}%")
else:
    st.sidebar.success("✅ CORE BALANCED")

# --- 3. DATA TELEMETRY (2026 REAL-TIME) ---
@st.cache_data(ttl=3600)
def fetch_telemetry():
    # Tickers for 2026 market data
    # Gold: GC=F, DXY: DX-Y.NYB, 10Y: ^TNX, BTC: BTC-USD
    tickers = {"BTC": "BTC-USD", "Gold": "GC=F", "DXY": "DX-Y.NYB", "10Y": "^TNX"}
    data_points = {}
    
    for key, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2mo")
            current = hist['Close'].iloc[-1]
            prev_month = hist['Close'].iloc[-22] if len(hist) > 22 else hist['Close'].iloc[0]
            mom = ((current - prev_month) / prev_month) * 100
            data_points[key] = (current, mom)
        except:
            data_points[key] = (0.0, 0.0)
            
    # Global M2 (StreetStats Proxy for Jan 2026)
    data_points["M2"] = (98352.0, 0.17) # Value in Billions, MoM %
    return data_points

telemetry = fetch_telemetry()

# Data Points for MELT Logic
M_SCORE, E_SCORE, L_SCORE, T_SCORE = 20.0, 29.0, 54.0, 35.0
final_score = (M_SCORE * norm_m) + (E_SCORE * norm_e) + (L_SCORE * norm_l) + (T_SCORE * norm_t)

def get_risk_meta(score):
    if score < 20: return "MELT UP", "#006400"
    if score < 40: return "SAFE", "#00ffcc"
    if score < 60: return "CAUTIOUS", "#ffa500"
    if score < 80: return "DANGEROUS", "#ef4444"
    return "MELT DOWN", "#8b0000"

strategy, strategy_color = get_risk_meta(final_score)

# --- 4. THE NUCLEAR GAUGE ENGINE ---
def create_gauge(value, title, is_master=False):
    _, color = get_risk_meta(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'color': 'white', 'size': 55 if is_master else 30}, 'suffix': "%"},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': "white"},
            'bar': {'color': color, 'thickness': 0.6},
            'bgcolor': "#1a1a1a", 'borderwidth': 4, 'bordercolor': "#444",
            'steps': [{'range': [0, 20], 'color': 'rgba(0, 255, 204, 0.1)'},
                      {'range': [80, 100], 'color': 'rgba(239, 68, 68, 0.1)'}]
        }
    ))
    
    if is_master:
        fig.add_annotation(
            text=f"STATUS: {strategy}", x=0.5, y=0.18, showarrow=False,
            font=dict(size=30, color=strategy_color, family="Courier New"),
            bgcolor="rgba(0,0,0,0.9)", bordercolor=strategy_color, borderwidth=2, borderpad=10
        )
    
    fig.update_layout(
        title={'text': title, 'y': 0.9, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 24, 'color': '#00ffcc'}},
        paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Courier New"},
        margin=dict(l=30, r=30, t=80, b=30), height=550 if is_master else 260
    )
    return fig

# --- 5. INTERFACE LAYOUT ---
st.write("### MELT STATUS")
st.divider()

# Macro Telemetry Header
t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns(5)
def render_telemetry(col, label, val, mom, prefix="$", suffix=""):
    color = "#00ffcc" if mom >= 0 else "#ef4444"
    col.markdown(f"""<div class='telemetry-label'>{label}</div>
                 <div class='telemetry-val'>{prefix}{val:,.2f}{suffix}</div>
                 <div class='telemetry-change' style='color:{color}'>MoM: {mom:+.2f}%</div>""", unsafe_allow_html=True)

render_telemetry(t_col1, "BITCOIN", telemetry["BTC"][0], telemetry["BTC"][1])
render_telemetry(t_col2, "GOLD", telemetry["Gold"][0], telemetry["Gold"][1])
render_telemetry(t_col3, "DXY INDEX", telemetry["DXY"][0], telemetry["DXY"][1], prefix="")
render_telemetry(t_col4, "US 10Y YIELD", telemetry["10Y"][0], telemetry["10Y"][1], prefix="", suffix="%")
render_telemetry(t_col5, "GLOBAL M2", telemetry["M2"][0], telemetry["M2"][1], prefix="$", suffix="B")

st.divider()

# Master Dial
st.plotly_chart(create_gauge(final_score, "", True), use_container_width=True)

# Pillar Gauges
p1, p2, p3, p4 = st.columns(4)
with p1: st.plotly_chart(create_gauge(M_SCORE, f"MACRO ({w_m}%)"), use_container_width=True)
with p2: st.plotly_chart(create_gauge(E_SCORE, f"EMOTION ({w_e}%)"), use_container_width=True)
with p3: st.plotly_chart(create_gauge(L_SCORE, f"LEVERAGE ({w_l}%)"), use_container_width=True)
with p4: 
    st.plotly_chart(create_gauge(T_SCORE, f"TECHNICS ({w_t}%)"), use_container_width=True)
    st.markdown("<p class='sensor-warning'>⚠️ CBBI OFFLINE: FALLBACK ACTIVE</p>", unsafe_allow_html=True)

# --- 6. HISTORICAL LOG ---
st.write("### 📜 CORE LOG: 180-DAY RETROSPECTIVE")

@st.cache_data
def get_historical_table():
    dates = [datetime.now() - timedelta(days=x) for x in range(0, 180, 15)]
    # Mock index simulation for historical visualization
    data = {
        "Date": [d.strftime("%Y-%m-%d") for d in dates],
        "BTC Price": [f"${(95000 - i*1000 + np.random.randint(-2000, 2000)):,.2f}" for i in range(len(dates))],
        "MELT Index": [np.random.randint(25, 65) for _ in range(len(dates))]
    }
    df = pd.DataFrame(data)
    # Add Status Mapping
    df['Status'] = df['MELT Index'].apply(lambda x: get_risk_meta(x)[0])
    return df

st.table(get_historical_table())

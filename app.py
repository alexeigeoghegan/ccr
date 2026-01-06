import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import urllib3
import plotly.graph_objects as go

# Disable SSL warnings to ensure smooth API handshakes
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Crypto Cycle Risk", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 40px !important; font-weight: 700 !important; }
    .stAlert { border: none; padding: 25px; border-radius: 15px; font-size: 32px; font-weight: 900; text-align: center; color: white !important; }
    .logic-box { background-color: #161b22; padding: 15px; border-radius: 10px; border-left: 5px solid #00ffcc; margin-bottom: 10px; font-size: 14px; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC: RISK NORMALIZATION ---
def norm_risk(val, sensitivity, inv=False):
    """
    Normalizes a value into a 0-100 risk score.
    Sensitivity defines the 'Max Risk' (100) or 'Max Safety' (0) threshold.
    """
    try:
        score = (float(val) / float(sensitivity)) * 100
        score = max(min(score, 100), 0)
        return (100 - score) if inv else score
    except: return 50.0

@st.cache_data(ttl=3600)
def get_data():
    # 2026 Baseline Snapshot (Manual Fallbacks)
    d = {'btc': 93246, 'dxy': 98.60, 'yield': 4.18, 'oil': 57.0, 'gold': 4506, 'fgi': 44, 'cbbi': 55, 
         'm2_mom': 0.35, 'cap': '3.2T', 'dom': '58.4%', 'etf': 1.2, 'fund': 0.01, 'ssr': 12.0}
    try:
        # Fetch 2 months for Raw MoM comparison
        data = yf.download(["BTC-USD", "DX-Y.NYB", "^TNX", "CL=F", "GC=F"], period="2mo", progress=False)['Close'].ffill().dropna()
        
        def get_raw_mom(col):
            curr = data[col].iloc[-1]
            prev = data[col].iloc[-22] # 22 trading days = 1 month
            return ((curr - prev) / prev) * 100, curr

        dxy_m, dxy_c = get_raw_mom("DX-Y.NYB")
        yld_m, yld_c = get_raw_mom("^TNX")
        oil_m, oil_c = get_raw_mom("CL=F")

        d.update({
            'btc': data["BTC-USD"].iloc[-1], 'dxy': dxy_c, 'yield': yld_c,
            'oil': oil_c, 'gold': data["GC=F"].iloc[-1],
            'dxy_mom': dxy_m, 'yld_mom': yld_m, 'oil_mom': oil_m
        })
    except:
        d.update({'dxy_mom': 0.46, 'yld_mom': 0.72, 'oil_mom': 3.06})
    return d

d = get_data()

# --- 3. SIDEBAR: GOLDEN SETTINGS (ALARM THRESHOLDS) ---
if st.sidebar.button("Reset to Defaults"):
    st.rerun()

st.sidebar.markdown("### Sensitivity Settings")
st.sidebar.info("These sliders define the 'Max Risk' threshold for each metric.")

# Golden Settings for 2026
s_dxy = st.sidebar.slider("DXY MoM Sensitivity (%)", 0.5, 5.0, 2.5) 
s_yld = st.sidebar.slider("10Y Yield MoM Sensitivity (%)", 1.0, 10.0, 5.0)
s_oil = st.sidebar.slider("Oil MoM Sensitivity (%)", 2.0, 20.0, 12.0)
s_m2  = st.sidebar.slider("M2 MoM Liquidity Target (%)", 0.1, 2.0, 0.8)
s_etf = st.sidebar.slider("ETF MoM Target (%)", 1.0, 10.0, 4.0)
s_fnd = st.sidebar.slider("Funding Max Risk (%)", 0.01, 0.2, 0.08)

# --- 4. PILLAR SCORING ENGINE ---
# MACRO: 50% Financial Momentum / 50% Liquidity Growth
risk_mac_fin = (norm_risk(d['dxy_mom'], s_dxy) + norm_risk(d['yld_mom'], s_yld) + norm_risk(d['oil_mom'], s_oil)) / 3
risk_mac_liq = norm_risk(d['m2_mom'], s_m2, inv=True) 
risk_mac = int(round(risk_mac_fin * 0.5 + risk_mac_liq * 0.5))

risk_sen = int(d['fgi']) 
risk_tec = int(d['cbbi']) 
risk_ado = int(round(norm_risk(d['etf'], s_etf, inv=True)))
risk_str = int(round(norm_risk(d['fund'], s_fnd)))

# TOTAL SCORE (WEIGHTED)
total_score = int(round((risk_mac*0.4) + (risk_sen*0.2) + (risk_tec*0.2) + (risk_ado*0.1) + (risk_str*0.1)))

# Color & Action Logic
if total_score < 35: act_label, act_color, g_color = "ACCUMULATE", "#006400", "#00ffcc"
elif total_score < 70: act_label, act_color, g_color = "HOLD", "#8B8000", "#ffff00"
else: act_label, act_color, g_color = "TAKE PROFITS / HEDGE", "#8B0000", "#ff4b4b"

# --- 5. UI: GAUGE & ACTION ---
st.title("Crypto Cycle Risk")

col_g, col_a = st.columns([2, 1])
with col_g:
    fig = go.Figure(go.Indicator(mode="gauge+number", value=total_score,
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': g_color},
               'steps': [{'range': [0, 35], 'color': '#002200'},
                         {'range': [35, 70], 'color': '#222200'},
                         {'range': [70, 100], 'color': '#220000'}]}))
    fig.update_layout(paper_bgcolor='#0e1117', font={'color': "white"}, height=320, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_a:
    st.write("##")
    st.markdown(f'<div class="stAlert" style="background-color:{act_color};">{act_label}</div>', unsafe_allow_html=True)

# --- 6. PERFORMANCE PILLARS ---
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)

def draw_pill(label, val):
    clr = "#00ffcc" if val < 35 else "#ffff00" if val < 70 else "#ff4b4b"
    st.markdown(f"**{label}** <br> <span style='color:{clr}; font-size:42px; font-weight:bold;'>{val}</span>", unsafe_allow_html=True)

with c1: draw_pill("MACRO 40%", risk_mac)
with c2: draw_pill("SENTIMENT 20%", risk_sen)
with c3: draw_pill("TECHNICALS 20%", risk_tec)
with c4: draw_pill("ADOPTION 10%", risk_ado)
with c5: draw_pill("STRUCTURE 10%", risk_str)

# --- 7. METHODOLOGY (DETAILED CALCULATION) ---
st.markdown("---")
st.subheader("Methodology")
l1, l2 = st.columns(2)

with l1:
    st.markdown(f"""
    <div class="logic-box">
        <b>1. Macro (40% Weight):</b> Split 50% Financial Momentum / 50% Liquidity Growth.<br>
        • Momentum: Average risk of DXY (+{d['dxy_mom']:.2f}%), Yields (+{d['yld_mom']:.2f}%), and Oil (+{d['oil_mom']:.2f}%). Math: <i>(MoM % / Sensitivity Slider) * 100</i>.<br>
        • Liquidity: M2 MoM growth. {s_m2}% target = 0 Risk; 0% growth = 100 Risk.
    </div>
    <div class="logic-box">
        <b>2. Sentiment (20% Weight):</b> 1:1 mapping to the Fear & Greed Index. High values signal extreme retail exuberance.
    </div>
    """, unsafe_allow_html=True)

with l2:
    st.markdown(f"""
    <div class="logic-box">
        <b>3. Technicals (20% Weight):</b> 1:1 mapping to the CBBI Index. Uses 11 on-chain oscillators to track historical cycle peaks.
    </div>
    <div class="logic-box">
        <b>4. Adoption & Structure (20% Weight):</b><br>
        • Adoption (10%): ETF MoM Net Inflow. Math: <i>(1 - (Actual Inflow / {s_etf}% Target)) * 100</i>.<br>
        • Structure (10%): Funding Rate velocity. 0% baseline = 0 Risk; {s_fnd}% = 100 Risk.
    </div>
    """, unsafe_allow_html=True)

# --- 8. SIDEBAR DATA FEED ---
st.sidebar.markdown("---")
st.sidebar.write(f"Bitcoin: `${d.get('btc',0):,.0f}`")
st.sidebar.write(f"DXY: `{d.get('dxy',0):.2f}` (`{d.get('dxy_mom',0):+.2f}%` MoM)")
st.sidebar.write(f"10Y Yield: `{d.get('yield',0):.2f}%` (`{d.get('yld_mom',0):+.2f}%`)")
st.sidebar.write(f"Oil: `${d.get('oil',0):.1f}` (`{d.get('oil_mom',0):+.2f}%`)")
st.sidebar.write(f"Gold: `${d.get('gold',0):,.0f}`")
st.sidebar.write(f"Global M2: `{d.get('m2_mom')}%`")
st.sidebar.write(f"Total Cap: `{d.get('cap')}`")
st.sidebar.write(f"BTC Dom: `{d.get('dom')}`")
st.sidebar.write(f"Fear & Greed: `{d.get('fgi')}`")
st.sidebar.write(f"CBBI Index: `{d.get('cbbi')}`")
st.sidebar.write(f"ETF Inflow: `{d.get('etf')}%`")
st.sidebar.write(f"Funding: `{d.get('fund')}%`")
st.sidebar.write(f"SSR Ratio: `{d.get('ssr')}`")

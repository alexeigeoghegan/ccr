import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import urllib3
import plotly.graph_objects as go

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Crypto Cycle Risk", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 40px !important; font-weight: 700 !important; }
    .stAlert { border: none; padding: 25px; border-radius: 15px; font-size: 32px; font-weight: 900; text-align: center; color: white !important; }
    .logic-box { background-color: #161b22; padding: 15px; border-radius: 10px; border-left: 5px solid #00ffcc; margin-bottom: 10px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOMENTUM LOGIC (Normalization of % Changes) ---
def norm_mom_risk(change_pct, min_expected, max_expected, inv=False):
    """
    Normalizes a % change. 
    High Risk = Positive Change (for DXY, Yields).
    Low Risk = Positive Change (for M2, BTC Inflows).
    """
    try:
        # Clip the change to a realistic monthly range (-5% to +5% for example)
        change_pct = max(min(change_pct, max_expected), min_expected)
        # Scale to 0-100
        score = ((change_pct - min_expected) / (max_expected - min_expected)) * 100
        return (100 - score) if inv else score
    except: return 50.0

@st.cache_data(ttl=3600)
def get_data():
    d = {'btc': 98500, 'dxy': 102, 'yield': 4.2, 'oil': 75, 'gold': 4470, 'fgi': 44, 'cbbi': 55, 
         'm2_mom': 0.35, 'cap': '3.2T', 'dom': '58.4%', 'etf': 1.2, 'fund': 0.01, 'ssr': 12.0}
    try:
        # Fetch 2 months for MoM baseline
        data = yf.download(["BTC-USD", "DX-Y.NYB", "^TNX", "CL=F", "GC=F"], period="2mo", progress=False)['Close'].ffill().dropna()
        
        def get_mom(col):
            curr, prev = data[col].iloc[-1], data[col].iloc[-22]
            return ((curr - prev) / prev) * 100

        d.update({
            'btc': data["BTC-USD"].iloc[-1], 'dxy': data["DX-Y.NYB"].iloc[-1], 
            'yield': data["^TNX"].iloc[-1], 'oil': data["CL=F"].iloc[-1], 
            'gold': data["GC=F"].iloc[-1],
            'dxy_mom': get_mom("DX-Y.NYB"), 'yld_mom': get_mom("^TNX"), 'oil_mom': get_mom("CL=F")
        })
    except:
        d.update({'dxy_mom': 0.0, 'yld_mom': 0.0, 'oil_mom': 0.0})
    return d

d = get_data()

# --- 3. PILLAR SCORING (BASED ON CHANGE) ---

# MACRO (40%) - Normalizing against a +/- 2% MoM window for Macro assets
# If DXY drops 2%, norm_mom_risk(-2, -2, 2) = 0 (Low Risk)
risk_mac_fin = (norm_mom_risk(d['dxy_mom'], -2, 2) + 
                norm_mom_risk(d['yld_mom'], -5, 5) + 
                norm_mom_risk(d['oil_mom'], -10, 10)) / 3
# M2 (Positive change = Low risk, so inv=True)
risk_mac_liq = norm_mom_risk(d['m2_mom'], 0, 1.0, inv=True) 
risk_mac = int(round(risk_mac_fin * 0.5 + risk_mac_liq * 0.5))

risk_sen = int(d['fgi']) # Absolute sentiment remains key for cycle top
risk_tec = int(d['cbbi']) # Absolute cycle maturity

# ADOPTION (10%) - Net Inflow change (Rising inflows = Low risk)
risk_ado = int(round(norm_mom_risk(d['etf'], -2, 5, inv=True)))

# STRUCTURE (10%) - Rising funding = Rising risk
risk_str = int(round(norm_mom_risk(d['fund'] - 0.01, -0.01, 0.05)))

total_score = int(round((risk_mac*0.4) + (risk_sen*0.2) + (risk_tec*0.2) + (risk_ado*0.1) + (risk_str*0.1)))

# Color Logic
if total_score < 35: act_label, act_color, gauge_color = "ACCUMULATE", "#006400", "#00ffcc"
elif total_score < 70: act_label, act_color, gauge_color = "HOLD / CAUTION", "#8B8000", "#ffff00"
else: act_label, act_color, gauge_color = "TAKE PROFITS / HEDGE", "#8B0000", "#ff4b4b"

# --- 4. TOP SECTION: GAUGE & ACTION ---
st.title("Crypto Cycle Risk")

col_g, col_a = st.columns([2, 1])
with col_g:
    fig = go.Figure(go.Indicator(mode="gauge+number", value=total_score,
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': gauge_color},
               'steps': [{'range': [0, 35], 'color': '#002200'},
                         {'range': [35, 70], 'color': '#222200'},
                         {'range': [70, 100], 'color': '#220000'}]}))
    fig.update_layout(paper_bgcolor='#0e1117', font={'color': "white"}, height=320, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_a:
    st.write("##")
    st.markdown(f'<div class="stAlert" style="background-color:{act_color};">{act_label}</div>', unsafe_allow_html=True)

# --- 5. PERFORMANCE PILLARS ---
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)

def draw_pill(label, val, mom_val):
    clr = "#00ffcc" if val < 35 else "#ffff00" if val < 70 else "#ff4b4b"
    arrow = "▲" if mom_val > 0 else "▼"
    st.markdown(f"**{label}** {arrow} <br> <span style='color:{clr}; font-size:42px; font-weight:bold;'>{val}</span>", unsafe_allow_html=True)

with c1: draw_pill("MACRO 40%", risk_mac, d['dxy_mom'])
with c2: draw_pill("SENTIMENT 20%", risk_sen, risk_sen - 50)
with c3: draw_pill("TECHNICALS 20%", risk_tec, 1)
with c4: draw_pill("ADOPTION 10%", risk_ado, d['etf'])
with c5: draw_pill("STRUCTURE 10%", risk_str, d['fund'])

# --- 6. LOGIC BREAKDOWN ---
st.markdown("---")
st.subheader("Pillar Derivation Logic")
l1, l2 = st.columns(2)
with l1:
    st.markdown(f"""<div class="logic-box"><b>Macro (40%):</b> Calculation is based on <b>MoM Change</b>. If DXY/Yields decrease, the score drops (Positive). If liquidity (M2) expands, score drops.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>Sentiment (20%):</b> Fear & Greed Index. Absolute values are used here as extreme psychological levels are fixed cycle markers.</div>""", unsafe_allow_html=True)
with l2:
    st.markdown(f"""<div class="logic-box"><b>Adoption (10%):</b> MoM momentum of BTC ETF inflows. Rising inflows lead to a lower risk score.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>Structure (10%):</b> Change in Funding Rates. High-velocity increases in leverage spike the risk score.</div>""", unsafe_allow_html=True)

# --- 7. SIDEBAR ---
st.sidebar.write(f"Bitcoin: `${d.get('btc',0):,.0f}`")
st.sidebar.write(f"DXY Index: `{d.get('dxy',0):.2f}` (`{d.get('dxy_mom',0):+.2f}%` MoM)")
st.sidebar.write(f"10Y Yield: `{d.get('yield',0):.2f}%` (`{d.get('yld_mom',0):+.2f}%` MoM)")
st.sidebar.write(f"Oil: `${d.get('oil',0):.1f}` (`{d.get('oil_mom',0):+.2f}%` MoM)")
st.sidebar.write(f"Global M2 (MoM): `{d.get('m2_mom')}%`")
st.sidebar.write(f"Total Cap: `{d.get('cap')}`")
st.sidebar.write(f"BTC Dom: `{d.get('dom')}`")
st.sidebar.write(f"Fear & Greed: `{d.get('fgi')}`")
st.sidebar.write(f"CBBI Index: `{d.get('cbbi')}`")
st.sidebar.write(f"ETF BTC Inflow: `{d.get('etf')}%`")
st.sidebar.write(f"Funding Rates: `{d.get('fund')}%`")
st.sidebar.write(f"SSR Ratio: `{d.get('ssr')}`")

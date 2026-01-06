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
    .logic-box { background-color: #161b22; padding: 15px; border-radius: 10px; border-left: 5px solid #00ffcc; margin-bottom: 10px; font-size: 14px; line-height: 1.6; min-height: 120px; }
    .instr-box { background-color: #0e1117; padding: 20px; border: 1px solid #30363d; border-radius: 15px; margin-bottom: 20px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC: RISK NORMALIZATION ---
def norm_risk(val, sensitivity, inv=False):
    try:
        score = (float(val) / float(sensitivity)) * 100
        score = max(min(score, 100), 0)
        return (100 - score) if inv else score
    except: return 50.0

@st.cache_data(ttl=3600)
def get_data():
    # 2026 Baseline Snapshot
    d = {'btc': 93246, 'dxy': 98.60, 'yield': 4.18, 'oil': 57.0, 'gold': 4506, 'fgi': 44, 'cbbi': 55, 
         'm2_mom': 0.35, 'cap': '3.2T', 'dom': '58.4%', 'etf': 1.2, 'stable_growth': 2.1, 'fund': 0.01, 'ssr': 12.0}
    try:
        data = yf.download(["BTC-USD", "DX-Y.NYB", "^TNX", "CL=F", "GC=F"], period="2mo", progress=False)['Close'].ffill().dropna()
        def get_mom(col):
            curr, prev = data[col].iloc[-1], data[col].iloc[-22]
            return ((curr - prev) / prev) * 100, curr
        dxy_m, dxy_c = get_mom("DX-Y.NYB")
        yld_m, yld_c = get_mom("^TNX")
        oil_m, oil_c = get_mom("CL=F")
        d.update({'btc': data["BTC-USD"].iloc[-1], 'dxy': dxy_c, 'yield': yld_c, 'oil': oil_c, 'gold': data["GC=F"].iloc[-1],
                  'dxy_mom': dxy_m, 'yld_mom': yld_m, 'oil_mom': oil_m})
    except:
        d.update({'dxy_mom': 0.46, 'yld_mom': 0.72, 'oil_mom': 3.06})
    return d

d = get_data()

# --- 3. FIXED GOLDEN SETTINGS ---
S_DXY, S_YLD, S_OIL, S_M2, S_ETF, S_STB, S_FND = 2.5, 5.0, 12.0, 0.8, 4.0, 5.0, 0.08

# --- 4. PILLAR SCORING ---
risk_mac_fin = (norm_risk(d['dxy_mom'], S_DXY) + norm_risk(d['yld_mom'], S_YLD) + norm_risk(d['oil_mom'], S_OIL)) / 3
risk_mac_liq = norm_risk(d['m2_mom'], S_M2, inv=True) 
risk_mac = int(round(risk_mac_fin * 0.5 + risk_mac_liq * 0.5))

risk_sen, risk_tec = int(d['fgi']), int(d['cbbi']) 

# Adoption: 50% ETF flows / 50% Stablecoin Supply Growth
risk_ado_etf = norm_risk(d['etf'], S_ETF, inv=True)
risk_ado_stb = norm_risk(d['stable_growth'], S_STB, inv=True)
risk_ado = int(round(risk_ado_etf * 0.5 + risk_ado_stb * 0.5))

risk_str = int(round(norm_risk(d['fund'], S_FND)))

total_score = int(round((risk_mac*0.4) + (risk_sen*0.2) + (risk_tec*0.2) + (risk_ado*0.1) + (risk_str*0.1)))

if total_score < 35: act_label, act_color, g_color = "ACCUMULATE", "#006400", "#00ffcc"
elif total_score < 70: act_label, act_color, g_color = "HOLD", "#8B8000", "#ffff00"
else: act_label, act_color, g_color = "TAKE PROFITS / HEDGE", "#8B0000", "#ff4b4b"

# --- 5. UI: HEADER & INSTRUCTIONS ---
st.title("Crypto Cycle Risk")
st.markdown(f"""
    <div class="instr-box">
        <b>Purpose:</b> This dashboard is designed for monthly strategic rebalancing. It aggregates Macro, Sentiment, Technical, and On-Chain data to determine if you should be <b>Accumulating</b> (buying spot), <b>Holding</b>, or <b>Hedging</b> (moving to stables).
        <br><i><b>Disclaimer:</b> Not financial advice. Data for educational purposes only.</i>
    </div>
    """, unsafe_allow_html=True)

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

# --- 6. METHODOLOGY ---
st.markdown("---")
st.subheader("Methodology")
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.markdown(f"""<div class="logic-box"><b>1. Macro (40%):</b> 50% weight on <i>((Actual MoM % / Threshold %) * 100)</i> for DXY ({S_DXY}%), Yields ({S_YLD}%), and Oil ({S_OIL}%). 50% weight on M2 MoM growth vs {S_M2}% target.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>4. Adoption (10%):</b> 50% weight on ETF MoM Net Inflow ({S_ETF}% Target). 50% weight on Stablecoin Supply Expansion ({S_STB}% Target). Both calculated as <i>(1 - (Actual / Target)) * 100</i>.</div>""", unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""<div class="logic-box"><b>2. Sentiment (20%):</b> Direct 1:1 mapping of the Fear & Greed Index. Scores above 70 contribute significantly to 'Cycle Risk' regardless of macro tailwinds.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>5. Structure (10%):</b> Linear calculation of Funding Rate risk: <i>(Current Rate / {S_FND}% Max) * 100</i>. Focuses on identifying leveraged 'blow-off' tops.</div>""", unsafe_allow_html=True)

with m_col3:
    st.markdown(f"""<div class="logic-box"><b>3. Technicals (20%):</b> Direct 1:1 mapping of the CBBI Index. Aggregates technical oscillators to find cyclical exhaustion points.</div>""", unsafe_allow_html=True)

# --- 7. SIDEBAR DATA FEED ---
st.sidebar.write(f"Bitcoin: `${d.get('btc',0):,.0f}`")
st.sidebar.write(f"DXY Index: `{d.get('dxy',0):.2f}` (`{d.get('dxy_mom',0):+.2f}%`)")
st.sidebar.write(f"10Y Yield: `{d.get('yield',0):.2f}%` (`{d.get('yld_mom',0):+.2f}%`)")
st.sidebar.write(f"Oil: `${d.get('oil',0):.1f}` (`{d.get('oil_mom',0):+.2f}%`)")
st.sidebar.write(f"Global M2: `{d.get('m2_mom')}%`")
st.sidebar.write(f"Fear & Greed: `{d.get('fgi')}`")
st.sidebar.write(f"CBBI Index: `{d.get('cbbi')}`")
st.sidebar.write(f"ETF Inflow: `{d.get('etf')}%`")
st.sidebar.write(f"Stablecoin Growth: `{d.get('stable_growth')}%`")
st.sidebar.write(f"Funding: `{d.get('fund')}%`")

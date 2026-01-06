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

# --- 2. CORE LOGIC ---
def norm_risk(val, mi, ma, inv=False):
    try:
        val = float(val)
        val = max(min(val, ma), mi)
        score = ((val - mi) / (ma - mi)) * 100
        return (100 - score) if inv else score
    except: return 50.0

@st.cache_data(ttl=3600)
def get_data():
    d = {'btc': 98500, 'dxy': 102, 'yield': 4.2, 'oil': 75, 'gold': 4470, 'fgi': 44, 'cbbi': 55, 
         'm2_mom': 0.35, 'cap': '3.2T', 'dom': '58.4%', 'etf': 1.2, 'fund': 0.01, 'ssr': 12.0}
    try:
        # Fetch 2 months to calculate MoM changes
        data = yf.download(["BTC-USD", "DX-Y.NYB", "^TNX", "CL=F", "GC=F"], period="2mo", progress=False)['Close'].ffill().dropna()
        
        # Calculate MoM % Changes
        def get_mom(col):
            curr = data[col].iloc[-1]
            prev = data[col].iloc[-22] # Approx 1 trading month ago
            return ((curr - prev) / prev) * 100

        d.update({
            'btc': data["BTC-USD"].iloc[-1], 'dxy': data["DX-Y.NYB"].iloc[-1], 
            'yield': data["^TNX"].iloc[-1], 'oil': data["CL=F"].iloc[-1], 
            'gold': data["GC=F"].iloc[-1],
            'dxy_mom': get_mom("DX-Y.NYB"), 'yld_mom': get_mom("^TNX"), 'oil_mom': get_mom("CL=F"),
            'prev_macro': data.iloc[-22] # To compare pillar momentum
        })
    except:
        d.update({'dxy_mom': 0.1, 'yld_mom': -0.2, 'oil_mom': 1.5})
    return d

d = get_data()

# --- 3. PILLAR & TOTAL SCORING ---
# Individual Risks (0-100)
risk_mac = int(round((norm_risk(d['dxy'],98,108)*0.33 + norm_risk(d['yield'],3,5)*0.33 + norm_risk(d['oil'],65,95)*0.34)*0.5 + norm_risk(d['m2_mom'],0,1.0,True)*0.5))
risk_sen = int(d['fgi'])
risk_tec = int(d['cbbi'])
risk_ado = int(round(norm_risk(d['etf'],-1,5,True)))
risk_str = int(round(norm_risk(d['fund'],0,0.06)*0.5 + norm_risk(d['ssr'],8,22)*0.5))

total_score = int(round((risk_mac*0.4) + (risk_sen*0.2) + (risk_tec*0.2) + (risk_ado*0.1) + (risk_str*0.1)))

# Color Logic Setup
if total_score < 35: 
    act_label, act_color, gauge_color = "ACCUMULATE", "#006400", "#00ffcc"
    st_func = st.success
elif total_score < 70: 
    act_label, act_color, gauge_color = "HOLD / CAUTION", "#8B8000", "#ffff00"
    st_func = st.warning
else: 
    act_label, act_color, gauge_color = "TAKE PROFITS / HEDGE", "#8B0000", "#ff4b4b"
    st_func = st.error

# --- 4. TOP SECTION: GAUGE & ACTION ---
st.title("Crypto Cycle Risk")

col_g, col_a = st.columns([2, 1])
with col_g:
    fig = go.Figure(go.Indicator(mode="gauge+number", value=total_score,
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': gauge_color},
               'steps': [{'range': [0, 35], 'color': '#003300'},
                         {'range': [35, 70], 'color': '#333300'},
                         {'range': [70, 100], 'color': '#330000'}]}))
    fig.update_layout(paper_bgcolor='#0e1117', font={'color': "white"}, height=320, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_a:
    st.write("##")
    # Action box colored consistent with the score
    st.markdown(f'<div class="stAlert" style="background-color:{act_color};">{act_label}</div>', unsafe_allow_html=True)

# --- 5. PERFORMANCE PILLARS WITH MOMENTUM ---
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)

def draw_pill(label, val, trend_up=True):
    clr = "#00ffcc" if val < 35 else "#ffff00" if val < 70 else "#ff4b4b"
    arrow = "▲" if trend_up else "▼"
    st.markdown(f"**{label}** {arrow} <br> <span style='color:{clr}; font-size:42px; font-weight:bold;'>{val}</span>", unsafe_allow_html=True)

# Momentum logic: Is risk higher today than 1 month ago?
with c1: draw_pill("MACRO 40%", risk_mac, trend_up=(d['dxy_mom'] > 0))
with c2: draw_pill("SENTIMENT 20%", risk_sen, trend_up=(risk_sen > 40)) # Static check for sentiment trend
with c3: draw_pill("TECHNICALS 20%", risk_tec, trend_up=True) # CBBI typically trends up in bull
with c4: draw_pill("ADOPTION 10%", risk_ado, trend_up=(d['etf'] < 1.0)) # Risk up if inflows down
with c5: draw_pill("STRUCTURE 10%", risk_struct, trend_up=False) # Low funding/ssr means risk down

# --- 6. LOGIC BREAKDOWN ---
st.markdown("---")
st.subheader("Pillar Derivation Logic")
l1, l2 = st.columns(2)
with l1:
    st.markdown(f"""<div class="logic-box"><b>Macro (40%):</b> Risk increases when USD strengthens or M2 liquidity growth slows. MoM metrics for DXY/Yields are leading indicators.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>Sentiment (20%):</b> Measures irrational exuberance. Current score of {risk_sen} indicates moderate market fear/neutrality.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>Technicals (20%):</b> Uses the CBBI composite to track parabolic maturity. Scores above 70 indicate a high-risk cycle blow-off.</div>""", unsafe_allow_html=True)
with l2:
    st.markdown(f"""<div class="logic-box"><b>Adoption (10%):</b> Institutional absorption via Spot ETFs. High momentum reduces the overall cycle risk score.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>Structure (10%):</b> Market leverage health. Low funding and healthy SSR indicate structural stability.</div>""", unsafe_allow_html=True)

# --- 7. SIDEBAR DATA FEED ---
st.sidebar.write(f"Bitcoin: `${d.get('btc',0):,.0f}`")
st.sidebar.write(f"DXY Index: `{d.get('dxy',0):.2f}`")
st.sidebar.write(f"DXY MoM: `{d.get('dxy_mom',0):+.2f}%`")
st.sidebar.write(f"10Y Yield: `{d.get('yield',0):.2f}%`")
st.sidebar.write(f"10Y Yield MoM: `{d.get('yld_mom',0):+.2f}%`")
st.sidebar.write(f"Gold: `${d.get('gold',0):,.0f}`")
st.sidebar.write(f"Oil: `${d.get('oil',0):.1f}`")
st.sidebar.write(f"Oil MoM: `{d.get('oil_mom',0):+.2f}%`")
st.sidebar.write(f"M2 MoM: `{d.get('m2_mom')}%`")
st.sidebar.write(f"Total Cap: `{d.get('cap')}`")
st.sidebar.write(f"BTC Dom: `{d.get('dom')}`")
st.sidebar.write(f"Fear & Greed: `{d.get('fgi')}`")
st.sidebar.write(f"CBBI Index: `{d.get('cbbi')}`")
st.sidebar.write(f"ETF Inflow: `{d.get('etf')}%`")
st.sidebar.write(f"Funding: `{d.get('fund')}%`")
st.sidebar.write(f"SSR Ratio: `{d.get('ssr')}`")

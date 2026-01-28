import streamlit as st
import pandas as pd

# --- CONFIGURATION & UI STYLING ---
st.set_page_config(page_title="FLEET Index | Institutional Dashboard", layout="wide")

def apply_custom_style():
    st.markdown("""
        <style>
        /* Main background and text */
        .stApp {
            background-color: #0e1117;
            color: #ffffff;
        }
        
        /* Strategy Box Styling */
        .strategy-container {
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
            border: 1px solid #30363d;
        }
        
        .strategy-label {
            font-size: 1.2rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }
        
        .strategy-score {
            font-size: 4rem;
            font-weight: 800;
        }

        /* Category Row Styling */
        .category-row {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            background-color: #161b22;
            border-left: 5px solid #30363d;
        }

        .metric-table {
            width: 100%;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9rem;
        }
        
        .status-green { color: #2ecc71; border-left-color: #2ecc71 !important; }
        .status-orange { color: #f39c12; border-left-color: #f39c12 !important; }
        .status-red { color: #e74c3c; border-left-color: #e74c3c !important; }
        
        hr { border: 0.5px solid #30363d; }
        </style>
    """, unsafe_allow_html=True)

# --- CORE LOGIC (THE MATH) ---
def clamp(n, minn=0, maxn=100):
    return max(min(n, maxn), minn)

def calculate_fleet_index(data):
    # 1. Financials (Base 50)
    fin_score = 50 + (data['dxy_pct'] * 10) + (data['oil_pct'] * 1) + (data['ten_y_pct'] * 1)
    
    # 2. Liquidity (Base 50)
    liq_score = 50 + (data['m2_pct'] * -20) + (data['fed_liq_pct'] * -10) + (data['move_pct'] * 2)
    
    # 3. Exposure
    ssr_adj = 10 if data['ssr_change'] < 0 else -10
    exp_score = data['raw_cdri'] + ssr_adj
    
    # 4. Emotion & Technicals (Placeholder logic for the 20% weights)
    emo_score = data.get('emotion_raw', 50)
    tech_score = data.get('tech_raw', 50)

    # Clamping
    scores = {
        "Financials": clamp(fin_score),
        "Liquidity": clamp(liq_score),
        "Exposure": clamp(exp_score),
        "Emotion": clamp(emo_score),
        "Technicals": clamp(tech_score)
    }
    
    total_score = round(sum(scores.values()) / 5)
    return total_score, scores

# --- UI COMPONENTS ---
def render_strategy_box(total_score):
    if total_score <= 50:
        label, color, hex_code = "ACCUMULATE", "status-green", "#2ecc71"
    elif total_score <= 70:
        label, color, hex_code = "NEUTRAL", "status-orange", "#f39c12"
    else:
        label, color, hex_code = "TAKE PROFITS", "status-red", "#e74c3c"
    
    st.markdown(f"""
        <div class="strategy-container" style="border-top: 5px solid {hex_code}">
            <div class="strategy-label" style="color: {hex_code}">{label}</div>
            <div class="strategy-score">{total_score}</div>
        </div>
    """, unsafe_allow_html=True)

def render_category_row(name, score, breakdown_data):
    # Determine color based on individual score
    if score <= 50: color_class = "status-green"
    elif score <= 70: color_class = "status-orange"
    else: color_class = "status-red"

    with st.container():
        st.markdown(f"""
            <div class="category-row {color_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: bold; font-size: 1.1rem;">{name.upper()}</span>
                    <span style="font-size: 1.2rem; font-weight: bold;">{round(score, 1)}</span>
                </div>
                <hr>
                <table class="metric-table">
                    {" ".join([f"<tr><td>{m}</td><td style='text-align:right;'>{v}</td></tr>" for m, v in breakdown_data.items()])}
                </table>
            </div>
        """, unsafe_allow_html=True)

# --- MAIN APPLICATION ---
def main():
    apply_custom_style()
    
    st.title("FLEET Index")
    st.markdown("Quant-driven market regime analysis for professional allocation.")

    # Sidebar for Data Entry (Simulating API or Manual Inputs)
    with st.sidebar:
        st.header("Input Metrics (1m %)")
        dxy = st.number_input("DXY 1m % Change", value=1.2)
        oil = st.number_input("Oil 1m % Change", value=-2.5)
        ten_y = st.number_input("10Y Yield 1m % Change", value=0.5)
        m2 = st.number_input("Global M2 1m % Change", value=0.1)
        fed_liq = st.number_input("Fed Net Liq 1m % Change", value=-0.5)
        move = st.number_input("MOVE Index 1m % Change", value=5.0)
        cdri = st.slider("Raw CDRI Score", 0, 100, 45)
        ssr_momentum = st.number_input("SSR 1m Absolute Change", value=-2.0)
        
        st.divider()
        report_date = st.date_input("Data Reporting Date")

    # Data Dictionary for calculations
    input_data = {
        'dxy_pct': dxy, 'oil_pct': oil, 'ten_y_pct': ten_y,
        'm2_pct': m2, 'fed_liq_pct': fed_liq, 'move_pct': move,
        'raw_cdri': cdri, 'ssr_change': ssr_momentum,
        'emotion_raw': 42, 'tech_raw': 65 # Default placeholders
    }

    # Calculations
    total_score, cat_scores = calculate_fleet_index(input_data)

    # Strategy Box
    render_strategy_box(total_score)

    # Breakdown Layout
    col1, col2 = st.columns(2)
    
    with col1:
        render_category_row("Financials", cat_scores["Financials"], {
            "DXY (1m%)": f"{dxy}%",
            "Crude Oil (1m%)": f"{oil}%",
            "US10Y (1m%)": f"{ten_y}%"
        })
        render_category_row("Liquidity", cat_scores["Liquidity"], {
            "Global M2 (1m%)": f"{m2}%",
            "Fed Net Liq (1m%)": f"{fed_liq}%",
            "MOVE Index (1m%)": f"{move}%"
        })
        render_category_row("Exposure", cat_scores["Exposure"], {
            "Raw CDRI Score": cdri,
            "SSR Momentum Adj": "+10" if ssr_momentum < 0 else "-10"
        })

    with col2:
        render_category_row("Emotion", cat_scores["Emotion"], {
            "Put/Call Ratio": "0.85",
            "VIX Term Structure": "Contango"
        })
        render_category_row("Technicals", cat_scores["Technicals"], {
            "RSI (14)": "58",
            "Dist. from 200DMA": "+4.2%"
        })

    # Footer
    st.markdown(f"<p style='text-align: center; color: gray; margin-top: 50px;'>Data reporting date: {report_date}</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

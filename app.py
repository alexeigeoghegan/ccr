def main():
    # Fetch Data
    btc_price = fetch_btc_price()
    m = fetch_macro_m()
    e = fetch_emotion_e()
    l = fetch_leverage_l()
    t = fetch_technicals_t()

    # Weighted Calculation
    final_score = (m * 0.4) + (e * 0.2) + (l * 0.2) + (t * 0.2)
    strategy_label, strategy_color = get_risk_meta(final_score)

    # UI Header
    st.title("📊 MELT Index")
    st.markdown(f"**Bitcoin Market Cycle Risk Dashboard** | Price: `${btc_price:,.2f}`")
    st.divider()

    # Main Dial Row
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.plotly_chart(create_gauge(final_score, "MASTER RISK INDEX", is_master=True), use_container_width=True)

    with col_right:
        # Using a cleaner f-string approach to avoid SyntaxErrors
        st.markdown(
            f"""
            <div style="border: 2px solid {strategy_color}; border-radius: 15px; padding: 20px; text-align: center;">
                <p style="color: #888; margin: 0;">Current Strategy</p>
                <h1 style="color: {strategy_color}; font-size: 3rem; margin: 10px 0;">{strategy_label.upper()}</h1>
                <p style="color: white; font-size: 1.2rem;">Risk Score: <strong>{final_score:.1f} / 100</strong></p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.info(f"""
        **Methodology:**
        - **Macro (40%):** Global liquidity & rate cycles.
        - **Emotion (20%):** Sentiment & crowd behavior.
        - **Leverage (20%):** Derivatives & liquidation risk.
        - **Technicals (20%):** On-chain cycle metrics (CBBI).
        """)

    # Pillar Row
    st.subheader("Component Pillars")
    p1, p2, p3, p4 = st.columns(4)
    
    with p1: st.plotly_chart(create_gauge(m, "Macro (M)"), use_container_width=True)
    with p2: st.plotly_chart(create_gauge(e, "Emotion (E)"), use_container_width=True)
    with p3: st.plotly_chart(create_gauge(l, "Leverage (L)"), use_container_width=True)
    with p4: st.plotly_chart(create_gauge(t, "Technicals (T)"), use_container_width=True)

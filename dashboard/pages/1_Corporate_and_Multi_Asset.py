import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Corporate & Multi-Asset Risk", layout="wide")
st.title("📈 Corporate & Multi-Asset Risk")

API_BASE = "http://127.0.0.1:8000/api/v1/risk"

st.markdown("Enter a global ticker (e.g., `AAPL`, `RELIANCE.NS`, `SPY`, `^TNX`) to compute institutional risk metrics.")

col1, col2 = st.columns([1, 2])
with col1:
    ticker = st.text_input("Ticker Symbol", value="AAPL")
    analyze_btn = st.button("Run Risk Analysis")

if analyze_btn:
    with st.spinner(f"Analyzing {ticker} via Credence-MertonX API..."):
        try:
            resp = requests.get(f"{API_BASE}/multi-asset/{ticker}", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"Analysis Complete: {data['asset_type']}")
                
                if data['asset_type'] == 'EQUITY':
                    metrics = data['metrics']
                    st.subheader(f"Merton Model Results: {ticker}")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Distance to Default (RN)", f"{metrics['DD_rn']:.2f}")
                    c2.metric("Probability of Default (RN)", f"{metrics['PD_rn']:.4%}")
                    cal_pd = metrics.get('PD_calibrated', None)
                    cal_str = f"{cal_pd:.4%}" if cal_pd is not None else "N/A"
                    c3.metric("Calibrated EDF", cal_str)
                    c4.metric("Asset Volatility", f"{metrics['sigma_V']:.2%}")
                    
                    if metrics.get('dd_timeseries'):
                        ts = metrics['dd_timeseries']
                        df_ts = pd.DataFrame(list(ts.items()), columns=['Date', 'DD'])
                        fig = px.line(df_ts, x='Date', y='DD', title='Distance-to-Default Trajectory (90 Days)')
                        st.plotly_chart(fig, use_container_width=True)
                        
                elif data['asset_type'] == 'ETF':
                    st.subheader(f"ETF Risk Metrics: {ticker}")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Risk Tier", data['risk_tier'])
                    c2.metric("Annual Volatility", f"{data['annual_volatility']:.2%}")
                    c3.metric("Max Drawdown", f"{data['max_drawdown']:.2%}")
                    c4.metric("Sharpe Ratio", f"{data['sharpe_ratio']:.2f}")
                    
                elif data['asset_type'] == 'GOV_BOND':
                    st.subheader(f"Fixed Income Risk: {ticker}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Current Yield", f"{data['current_yield']:.2%}")
                    c2.metric("Modified Duration", f"{data['modified_duration']:.2f} yrs")
                    c3.metric("Convexity", f"{data['convexity']:.2f}")
                    st.info(f"Assessed Interest Rate Risk: **{data['risk_tier']}**")
                    
            else:
                st.error(f"Error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")
            st.warning("Please ensure the FastAPI backend is running (`uvicorn api.app:app --reload`).")

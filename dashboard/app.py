import streamlit as st

st.set_page_config(
    page_title="Credence-MertonX Dashboard",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Credence-MertonX")
st.markdown("""
### Institutional-Grade Credit Risk Platform

Welcome to the **Credence-MertonX** dashboard. This unified platform provides front-end access to the quantitative models and ML pipelines built across 4 distinct phases:

👈 **Select a module from the sidebar**

1. **Corporate & Multi-Asset Risk**
   - Merton/KMV Structural Models (Distance-to-Default)
   - Altman Z-Scores
   - ETF & Government Bond Metrics
2. **Retail & Mortgage Risk**
   - Expected Loss (EL) Pipeline
   - Probability of Default (PD) & Loss Given Default (LGD) scoring
   - Fannie Mae-style Synthetic Data Simulator
3. **ML Early Warning System**
   - GARCH(1,1) Volatility
   - Isotonic Regression Calibration
   - Trajectory Clustering (DTW)
""")

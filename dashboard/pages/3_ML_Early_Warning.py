import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="ML Early Warning System", layout="wide")
st.title("🚨 ML Early Warning System")

st.markdown("""
This module visualizes the two core machine learning enhancements to the classical Merton structural model.
""")

tab1, tab2 = st.tabs(["DTW Trajectory Clustering", "Isotonic Calibration (DD -> EDF)"])

with tab1:
    st.subheader("Dynamic Time Warping (DTW) + K-Means Clustering")
    st.markdown("Identifies deteriorating credit trajectories over a 90-day window, issuing proactive alerts before static thresholds are breached.")
    
    if st.button("Generate Demo Trajectories"):
        with st.spinner("Running DTW Clustering engine..."):
            import sys, os
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
            from model.clustering import DDTrajectoryClusterer
            
            clusterer = DDTrajectoryClusterer()
            demo_data = clusterer.generate_demo_trajectories(n_firms=15)
            alerts = clusterer.generate_alerts(demo_data)
            
            # Plot
            fig = go.Figure()
            for ticker, row in demo_data.iterrows():
                series = row['trajectory']
                cluster = row['cluster_label']
                color = "green" if cluster == "Improving" else "red" if cluster == "Deteriorating" else "gray"
                fig.add_trace(go.Scatter(y=series, mode='lines', name=f"{ticker} ({cluster})", line=dict(color=color, width=1 if color=="gray" else 3)))
                
            fig.update_layout(title="Distance-to-Default (DD) Trajectories (90 Days)", xaxis_title="Days", yaxis_title="Distance to Default")
            st.plotly_chart(fig, use_container_width=True)
            
            if alerts:
                st.warning("⚠️ Deterioration Alerts Triggered:")
                for alert in alerts:
                    st.write(f"- **{alert['ticker']}**: {alert['message']} (Severity: {alert['severity']})")
            else:
                st.success("No deteriorating trajectories detected.")

with tab2:
    st.subheader("Isotonic Regression (Fat-Tail Correction)")
    st.markdown("Maps theoretical Distance-to-Default to empirical Expected Default Frequency (EDF), correcting the naive normal distribution assumption.")
    
    if st.button("Show Calibration Curve"):
        with st.spinner("Fitting Isotonic Calibrator..."):
            from model.calibration import DDCalibrator
            from scipy.stats import norm
            
            cal = DDCalibrator()
            cal.fit_synthetic(n_samples=2000)
            
            dd_vals = np.linspace(0, 5, 100)
            naive_pd = norm.cdf(-dd_vals)
            calibrated_pd = cal.predict(dd_vals)
            
            df_plot = pd.DataFrame({
                'DD': dd_vals,
                'Naive N(-DD)': naive_pd,
                'Calibrated EDF': calibrated_pd
            })
            
            fig = px.line(df_plot, x='DD', y=['Naive N(-DD)', 'Calibrated EDF'], 
                          title='Empirical Calibration Curve (Log Scale)',
                          log_y=True)
            fig.update_yaxes(title="Probability of Default (PD)")
            st.plotly_chart(fig, use_container_width=True)

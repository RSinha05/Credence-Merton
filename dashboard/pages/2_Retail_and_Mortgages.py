import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Retail & Mortgage Risk", layout="wide")
st.title("🏠 Retail & Mortgage Risk")

API_BASE = "http://127.0.0.1:8000/api/v1/risk"

st.markdown("""
This module simulates a retail loan portfolio (e.g., Fannie Mae/Freddie Mac single-family loans) and routes it through the **Expected Loss Engine**.
$$ EL = PD \\times LGD \\times EAD $$
""")

num_loans = st.slider("Select Number of Synthetic Loans to Analyze", min_value=10, max_value=5000, value=100, step=10)
run_btn = st.button("Generate & Analyze Portfolio")

if run_btn:
    with st.spinner("Generating synthetic loan tape and analyzing via ML backend..."):
        try:
            # We use the python module directly here for data generation to send to API
            import sys, os
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
            from data.synthetic_mortgage import MortgageDataGenerator
            
            gen = MortgageDataGenerator()
            df = gen.generate_loan_tape(n_loans=num_loans)
            
            # Prepare payload
            loans_payload = []
            for _, row in df.iterrows():
                loans_payload.append({
                    "loan_id": row['loan_id'],
                    "fico_score": float(row['fico_score']),
                    "ltv": float(row['ltv']),
                    "dti": float(row['dti']),
                    "loan_amount": float(row['loan_amount']),
                    "interest_rate": float(row['interest_rate']),
                    "term_months": int(row['term_months']),
                    "months_seasoned": 24 # assume 2 years seasoned for demo
                })
            
            resp = requests.post(f"{API_BASE}/retail/portfolio", json={"loans": loans_payload}, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                
                st.success("Portfolio Analysis Complete")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Exposure at Default (EAD)", f"${data['portfolio_total_ead']:,.2f}")
                c2.metric("Portfolio Expected Loss (EL)", f"${data['portfolio_expected_loss']:,.2f}")
                el_pct = data['portfolio_expected_loss'] / data['portfolio_total_ead'] if data['portfolio_total_ead'] > 0 else 0
                c3.metric("Expected Loss %", f"{el_pct:.2%}")
                
                # Parse results
                results_df = pd.DataFrame(data['loan_results'])
                
                st.subheader("Distribution Analysis")
                c_chart1, c_chart2 = st.columns(2)
                with c_chart1:
                    fig_pd = px.histogram(results_df, x="pd", nbins=50, title="Probability of Default (PD) Distribution")
                    st.plotly_chart(fig_pd, use_container_width=True)
                with c_chart2:
                    fig_lgd = px.histogram(results_df, x="lgd", nbins=50, title="Loss Given Default (LGD) Distribution")
                    st.plotly_chart(fig_lgd, use_container_width=True)
                    
                st.subheader("Loan-Level Data")
                st.dataframe(results_df.head(100)) # show top 100
                
            else:
                st.error(f"Error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Failed to connect: {e}")

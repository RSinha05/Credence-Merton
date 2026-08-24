"""
Synthetic mortgage data generator module.
"""

import logging
import numpy as np
import pandas as pd

# Configure module logger
logger = logging.getLogger(__name__)

class MortgageDataGenerator:
    """
    Generates synthetic retail mortgage loan tapes for testing and modeling purposes.
    Simulates variables similar to public Fannie Mae/Freddie Mac datasets.
    """

    def generate_loan_tape(self, n_loans: int = 10000, seed: int = 42) -> pd.DataFrame:
        """
        Generate a realistic retail mortgage loan tape.

        Args:
            n_loans (int): The number of synthetic loans to generate.
            seed (int): Random seed for reproducibility.

        Returns:
            pd.DataFrame: A DataFrame containing the synthetic loan tape.
                          Includes FICO, LTV, DTI, loan amount, interest rate,
                          term, default outcomes, and recovery rates.
        """
        logger.info(f"Generating synthetic loan tape for {n_loans} loans with seed {seed}")
        np.random.seed(seed)

        # 1. Base Borrower and Loan Features
        # FICO: Normal distribution clipped between 300 and 850
        fico_score = np.clip(np.random.normal(700, 50, n_loans), 300, 850).astype(int)
        
        # LTV: Loan-to-Value ratio (mean 80, std 15, clipped 50 to 120)
        ltv = np.clip(np.random.normal(80, 15, n_loans), 50, 120)
        
        # DTI: Debt-to-Income ratio (mean 35, std 10, clipped 10 to 60)
        dti = np.clip(np.random.normal(35, 10, n_loans), 10, 60)
        
        # Loan Amount: Log-normal distribution (mean ~$300k)
        # exp(12.6) roughly equals 296,558
        loan_amount = np.random.lognormal(mean=12.6, sigma=0.4, size=n_loans)
        
        # Term: 15-year (180 months) or 30-year (360 months)
        term_months = np.random.choice([180, 360], size=n_loans, p=[0.2, 0.8])

        # 2. Interest Rate Pricing
        # Base rate + risk premiums based on FICO and LTV
        base_rate = 0.05
        fico_penalty = (850 - fico_score) * 0.0001
        ltv_penalty = np.maximum(0, (ltv - 80) * 0.0005)
        interest_rate = base_rate + fico_penalty + ltv_penalty

        # 3. Default Probability and Outcome (Target Variables)
        # Logistic probability based on FICO, LTV, and DTI
        # Intercept chosen to give roughly a 3-5% overall default rate
        score = -3.2 - 0.015 * (fico_score - 700) + 0.04 * (ltv - 80) + 0.05 * (dti - 35)
        default_prob = 1 / (1 + np.exp(-score))
        
        # Sample binomial outcome
        default_flag = np.random.binomial(1, default_prob)

        # 4. Recovery Rate
        # Highly dependent on LTV, generated for all records but mostly relevant upon default.
        # e.g., LTV 60 -> Base recovery 1.0, LTV 100 -> Base recovery 0.6
        base_recovery = 1.0 - (ltv - 60) / 100.0
        recovery_rate_noisy = np.random.normal(base_recovery, 0.1)
        recovery_rate = np.clip(recovery_rate_noisy, 0.0, 1.0)

        df = pd.DataFrame({
            'loan_id': np.arange(1, n_loans + 1),
            'fico_score': fico_score,
            'ltv': ltv,
            'dti': dti,
            'loan_amount': loan_amount,
            'interest_rate': interest_rate,
            'term_months': term_months,
            'default_prob': default_prob,
            'default_flag': default_flag,
            'recovery_rate': recovery_rate
        })
        
        actual_default_rate = df['default_flag'].mean()
        logger.info(f"Generation complete. Actual default rate: {actual_default_rate:.2%}")

        return df

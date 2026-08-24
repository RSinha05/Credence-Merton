"""
Retail Credit ML Models for the Credence-MertonX platform.

This module implements the Expected Loss (EL = PD x LGD x EAD) framework
for retail mortgages.
"""

import logging
from typing import Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import roc_auc_score, mean_squared_error

logger = logging.getLogger(__name__)

class RetailRiskEngine:
    """
    Engine for predicting Probability of Default (PD), Loss Given Default (LGD),
    Exposure at Default (EAD), and computing Expected Loss (EL).
    
    Formula:
        $$EL = PD \times LGD \times EAD$$
    """
    
    def __init__(self) -> None:
        """Initialize the Retail Risk Engine."""
        self.pd_model: Optional[xgb.XGBClassifier] = None
        self.lgd_model: Optional[xgb.XGBRegressor] = None
        
    def fit_pd_model(self, features: pd.DataFrame, labels: pd.Series) -> float:
        """
        Train an XGBoost Classifier for PD.
        
        Args:
            features (pd.DataFrame): Features including fico_score, ltv, dti, loan_amount, interest_rate.
            labels (pd.Series): Binary default flag (1 for default, 0 otherwise).
            
        Returns:
            float: Cross-validated ROC AUC score.
        """
        logger.info("Training PD model.")
        self.pd_model = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            use_label_encoder=False,
            eval_metric='logloss',
            random_state=42
        )
        
        # Calculate CV metrics
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(self.pd_model, features, labels, cv=cv, scoring='roc_auc')
        auc_score = float(np.mean(cv_scores))
        logger.info(f"PD Model CV ROC AUC: {auc_score:.4f}")
        
        # Fit on full data
        self.pd_model.fit(features, labels)
        
        return auc_score
        
    def fit_lgd_model(self, features: pd.DataFrame, recovery_rates: pd.Series) -> float:
        """
        Train an XGBoost Regressor for LGD (predicted via recovery rate).
        LGD = 1.0 - recovery_rate
        
        Args:
            features (pd.DataFrame): Input features.
            recovery_rates (pd.Series): Recovery rate between 0 and 1.
            
        Returns:
            float: RMSE of the recovery rate prediction.
        """
        logger.info("Training LGD model.")
        self.lgd_model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            objective='reg:logistic',
            random_state=42
        )
        
        self.lgd_model.fit(features, recovery_rates)
        
        predictions = self.lgd_model.predict(features)
        rmse = float(np.sqrt(mean_squared_error(recovery_rates, predictions)))
        logger.info(f"LGD Model RMSE: {rmse:.4f}")
        
        return rmse
        
    def calculate_ead(self, loan_amount: pd.Series, interest_rate: pd.Series, 
                      term_months: pd.Series, months_seasoned: pd.Series) -> pd.Series:
        """
        Calculate Exposure at Default (EAD) using standard mortgage amortization.
        
        Formula for remaining balance after m months:
        $$B_m = L \times \frac{(1 + r)^n - (1 + r)^m}{(1 + r)^n - 1}$$
        where L = loan_amount, r = monthly interest_rate, n = term_months, m = months_seasoned.
        
        Args:
            loan_amount (pd.Series): Original loan amount.
            interest_rate (pd.Series): Annual interest rate (e.g., 0.05 for 5%).
            term_months (pd.Series): Total term of the loan in months.
            months_seasoned (pd.Series): Number of months elapsed.
            
        Returns:
            pd.Series: Remaining principal balance (EAD).
        """
        logger.info("Calculating EAD.")
        
        r = interest_rate / 12.0
        n = term_months
        m = months_seasoned
        L = loan_amount
        
        # Handle division by zero for 0% interest rate
        factor_n = (1 + r) ** n
        factor_m = (1 + r) ** m
        
        # Remaining balance
        ead = L * (factor_n - factor_m) / (factor_n - 1)
        
        # Ensure it doesn't go below 0
        ead = np.maximum(ead, 0)
        return ead
        
    def predict_expected_loss(self, loan_features: pd.DataFrame, 
                              months_seasoned: pd.Series,
                              term_months: pd.Series) -> pd.DataFrame:
        """
        Predict PD, LGD, EAD, and Expected Loss (EL).
        
        Args:
            loan_features (pd.DataFrame): Features for PD/LGD models. Must include 'loan_amount' and 'interest_rate'.
            months_seasoned (pd.Series): Number of months since origination.
            term_months (pd.Series): Total term of the loan in months.
            
        Returns:
            pd.DataFrame: Contains PD, LGD, EAD, and Expected Loss.
        """
        logger.info("Predicting Expected Loss components.")
        if self.pd_model is None or self.lgd_model is None:
            raise ValueError("Models are not trained yet. Call fit_pd_model and fit_lgd_model first.")
            
        # Predict PD
        pd_preds = self.pd_model.predict_proba(loan_features)[:, 1]
        
        # Predict LGD (1 - recovery_rate)
        recovery_preds = self.lgd_model.predict(loan_features)
        recovery_preds = np.clip(recovery_preds, 0, 1)
        lgd_preds = 1.0 - recovery_preds
        
        # Calculate EAD
        ead_preds = self.calculate_ead(
            loan_amount=loan_features['loan_amount'],
            interest_rate=loan_features['interest_rate'],
            term_months=term_months,
            months_seasoned=months_seasoned
        )
        
        # Calculate Expected Loss
        el_preds = pd_preds * lgd_preds * ead_preds
        
        results = pd.DataFrame({
            'PD': pd_preds,
            'LGD': lgd_preds,
            'EAD': ead_preds,
            'expected_loss': el_preds
        }, index=loan_features.index)
        
        return results

    def save_models(self, pd_path: str, lgd_path: str) -> None:
        """
        Save the trained XGBoost models.
        
        Args:
            pd_path (str): File path to save PD model.
            lgd_path (str): File path to save LGD model.
        """
        if self.pd_model is not None:
            self.pd_model.save_model(pd_path)
            logger.info(f"Saved PD model to {pd_path}")
        if self.lgd_model is not None:
            self.lgd_model.save_model(lgd_path)
            logger.info(f"Saved LGD model to {lgd_path}")

    def load_models(self, pd_path: str, lgd_path: str) -> None:
        """
        Load trained XGBoost models from disk.
        
        Args:
            pd_path (str): File path to load PD model.
            lgd_path (str): File path to load LGD model.
        """
        self.pd_model = xgb.XGBClassifier()
        self.pd_model.load_model(pd_path)
        logger.info(f"Loaded PD model from {pd_path}")
        
        self.lgd_model = xgb.XGBRegressor()
        self.lgd_model.load_model(lgd_path)
        logger.info(f"Loaded LGD model from {lgd_path}")

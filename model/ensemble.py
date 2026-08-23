"""
Ensemble model combining Merton Distance to Default (DD) and Altman Z-Score.
"""

import logging
import math
from typing import Dict, Any, Optional
import pandas as pd

from model.merton import run_single_firm
from model.altman_z import run_altman_z

logger = logging.getLogger(__name__)

def compute_ensemble_risk(
    merton_results: Dict[str, Any],
    altman_results: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Combines Merton DD and Altman Z-Score into a unified risk assessment.
    
    Normalizes Z-Score to a PD-like probability using logistic mapping:
        pd_from_z = 1 / (1 + exp(z_score - 2.0))
        
    Args:
        merton_results: Output from model.merton.run_single_firm
        altman_results: Output from model.altman_z.run_altman_z
        weights: Optional custom weights. Defaults to {'merton_pd': 0.6, 'altman_z': 0.4}.
                 
    Returns:
        Dict with keys: 'ensemble_pd', 'merton_pd', 'altman_pd_proxy', 'risk_tier', 
        'models_agree', 'composite_score', 'confidence'.
    """
    if weights is None:
        weights = {'merton_pd': 0.6, 'altman_z': 0.4}
        
    w_merton = weights.get('merton_pd', 0.6)
    w_altman = weights.get('altman_z', 0.4)
    
    merton_pd = merton_results.get('pd', merton_results.get('default_probability', 0.0))
    z_score = altman_results.get('z_score', 2.0)
    
    # Normalize Z-Score to PD-like probability
    try:
        altman_pd_proxy = 1.0 / (1.0 + math.exp(z_score - 2.0))
    except OverflowError:
        altman_pd_proxy = 0.0 if z_score > 2.0 else 1.0
        
    ensemble_pd = w_merton * merton_pd + w_altman * altman_pd_proxy
    
    # Composite score: weighted average of normalized DD and Z
    dd = merton_results.get('dd', merton_results.get('distance_to_default', 0.0))
    composite_score = w_merton * dd + w_altman * z_score
    
    if ensemble_pd < 0.01:
        risk_tier = 'LOW'
    elif ensemble_pd < 0.05:
        risk_tier = 'MEDIUM'
    elif ensemble_pd < 0.15:
        risk_tier = 'HIGH'
    else:
        risk_tier = 'CRITICAL'
        
    # Check if models agree on risk tier
    def get_tier(pd_val: float) -> str:
        if pd_val < 0.01: return 'LOW'
        if pd_val < 0.05: return 'MEDIUM'
        if pd_val < 0.15: return 'HIGH'
        return 'CRITICAL'
        
    merton_tier = get_tier(merton_pd)
    altman_tier = get_tier(altman_pd_proxy)
    
    models_agree = (merton_tier == altman_tier)
    confidence = 0.9 if models_agree else 0.4
    
    logger.info(f"Ensemble risk: PD={ensemble_pd:.4f}, Tier={risk_tier}, Agree={models_agree}")
    
    return {
        'ensemble_pd': ensemble_pd,
        'merton_pd': merton_pd,
        'altman_pd_proxy': altman_pd_proxy,
        'risk_tier': risk_tier,
        'models_agree': models_agree,
        'composite_score': composite_score,
        'confidence': confidence
    }

def run_full_assessment(
    ticker: str, 
    equity_series: pd.Series, 
    D: float, 
    r: float, 
    market_cap: float, 
    T: float = 1.0
) -> Dict[str, Any]:
    """
    Runs both Merton and Altman, combines via ensemble. Single entry point for full firm analysis.
    
    Args:
        ticker: Company ticker symbol.
        equity_series: Historical equity market cap series (indexed by date).
        D: Default point (STD + 0.5 * LTD).
        r: Risk-free rate.
        market_cap: Current market capitalization.
        T: Time to maturity in years (default 1.0).
        
    Returns:
        Dict containing full assessment results from both models and ensemble.
    """
    logger.info(f"Running full risk assessment for {ticker}")
    
    # Run Merton
    merton_results = run_single_firm(
        equity_series=equity_series,
        D=D,
        r=r,
        T=T
    )
    
    # Run Altman
    altman_results = run_altman_z(
        ticker=ticker,
        market_cap=market_cap
    )
    
    # Bridge Merton result keys to what compute_ensemble_risk expects
    merton_for_ensemble = {
        'pd': merton_results.get('PD_rn', 0.0),
        'dd': merton_results.get('DD_rn', 0.0),
        'default_probability': merton_results.get('PD_rn', 0.0),
        'distance_to_default': merton_results.get('DD_rn', 0.0),
    }
    
    # Ensemble
    ensemble_results = compute_ensemble_risk(merton_for_ensemble, altman_results)
    
    return {
        'ticker': ticker,
        'merton': merton_results,
        'altman': altman_results,
        'ensemble': ensemble_results
    }


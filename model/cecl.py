import logging
import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, Any

logger = logging.getLogger(__name__)

SCENARIOS = {
    'baseline': {'weight': 0.40, 'vol_shock': 0.0, 'drift_shock': 0.0, 'spread_shock': 0.0},
    'adverse': {'weight': 0.35, 'vol_shock': 0.30, 'drift_shock': -0.05, 'spread_shock': 0.02},
    'severely_adverse': {'weight': 0.25, 'vol_shock': 0.60, 'drift_shock': -0.10, 'spread_shock': 0.05}
}

def condition_pd_term_structure(pd_term_structure: Dict[float, float], scenario: Dict[str, float]) -> Dict[float, float]:
    r"""
    Apply scenario shocks to the existing pd_term_structure.
    
    Formula:
    $$ PD_{shocked}(h) = \Phi( \Phi^{-1}(PD(h)) + vol\_shock \times \sqrt{h} + drift\_shock \times h ) $$
    
    Args:
        pd_term_structure: Dictionary mapping horizon h (float) to probability of default (float).
        scenario: Dictionary containing 'vol_shock' and 'drift_shock'.
        
    Returns:
        Dict[float, float]: The shocked PD term structure.
    """
    shocked_pd = {}
    vol_shock = scenario.get('vol_shock', 0.0)
    drift_shock = scenario.get('drift_shock', 0.0)
    
    for h, pd_val in pd_term_structure.items():
        # Avoid infinity with ppf
        if pd_val <= 0.0:
            pd_val = 1e-9
        elif pd_val >= 1.0:
            pd_val = 1.0 - 1e-9
            
        z = norm.ppf(pd_val)
        shocked_z = z + vol_shock * np.sqrt(h) + drift_shock * h
        shocked_pd_val = float(norm.cdf(shocked_z))
        
        # Clip to [0, 1]
        shocked_pd_val = max(0.0, min(1.0, shocked_pd_val))
        shocked_pd[h] = shocked_pd_val
        
    return shocked_pd

def compute_lifetime_pd(pd_term_structure: Dict[float, float]) -> float:
    r"""
    Compute cumulative lifetime PD from the term structure.
    
    Formulas:
    $$ Marginal(h_i) = 1 - \\frac{1 - cumPD(h_i)}{1 - cumPD(h_{i-1})} $$
    $$ Survival(h) = \prod (1 - Marginal(h_i)) $$
    $$ Lifetime\_PD = 1 - Survival(max\_horizon) $$
    
    Args:
        pd_term_structure: Dictionary mapping horizon to cumulative PD.
        
    Returns:
        float: The cumulative lifetime PD.
    """
    horizons = sorted(pd_term_structure.keys())
    if not horizons:
        return 0.0
        
    survival = 1.0
    prev_cum_pd = 0.0
    
    for h in horizons:
        cum_pd = pd_term_structure[h]
        # Calculate marginal PD
        if prev_cum_pd >= 1.0:
            marginal = 0.0
        else:
            marginal = 1.0 - (1.0 - cum_pd) / (1.0 - prev_cum_pd)
            
        # Ensure marginal is between 0 and 1
        marginal = max(0.0, min(1.0, marginal))
        
        survival *= (1.0 - marginal)
        prev_cum_pd = cum_pd
        
    lifetime_pd = 1.0 - survival
    return float(lifetime_pd)

def compute_cecl_expected_loss(merton_results: Dict[str, Any], lgd: float = 0.45, ead: float = 1.0) -> Dict[str, Any]:
    """
    Compute CECL expected loss by weighting lifetime PDs across scenarios.
    
    Args:
        merton_results: Dictionary containing 'pd_term_structure'.
        lgd: Loss Given Default (default 0.45).
        ead: Exposure At Default (default 1.0).
        
    Returns:
        Dictionary with scenario results, weighted lifetime PD, and CECL EL.
    """
    pd_term_structure = merton_results.get('pd_term_structure', {})
    
    scenario_results = {}
    weighted_lifetime_pd = 0.0
    
    for scenario_name, scenario_params in SCENARIOS.items():
        weight = scenario_params['weight']
        shocked_ts = condition_pd_term_structure(pd_term_structure, scenario_params)
        lifetime_pd = compute_lifetime_pd(shocked_ts)
        
        scenario_results[scenario_name] = {
            'lifetime_pd': lifetime_pd,
            'shocked_term_structure': shocked_ts
        }
        
        weighted_lifetime_pd += weight * lifetime_pd
        
    cecl_el = weighted_lifetime_pd * lgd * ead
    
    return {
        'scenario_results': scenario_results,
        'weighted_lifetime_pd': float(weighted_lifetime_pd),
        'cecl_expected_loss': float(cecl_el),
        'lgd': float(lgd),
        'ead': float(ead)
    }

def compute_panel_cecl(panel_results: Dict[str, Dict[str, Any]], lgd: float = 0.45) -> pd.DataFrame:
    """
    Compute CECL expected loss for a panel of firms.
    
    Args:
        panel_results: Dictionary mapping tickers to merton_results dictionaries.
        lgd: Loss Given Default.
        
    Returns:
        pd.DataFrame: DataFrame with CECL metrics per firm.
    """
    rows = []
    
    for ticker, merton_res in panel_results.items():
        cecl_res = compute_cecl_expected_loss(merton_res, lgd=lgd, ead=1.0)
        
        row = {
            'ticker': ticker,
            'baseline_lifetime_pd': cecl_res['scenario_results']['baseline']['lifetime_pd'],
            'adverse_lifetime_pd': cecl_res['scenario_results']['adverse']['lifetime_pd'],
            'severe_lifetime_pd': cecl_res['scenario_results']['severely_adverse']['lifetime_pd'],
            'weighted_lifetime_pd': cecl_res['weighted_lifetime_pd'],
            'cecl_el': cecl_res['cecl_expected_loss']
        }
        rows.append(row)
        
    if rows:
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(columns=['ticker', 'baseline_lifetime_pd', 'adverse_lifetime_pd', 'severe_lifetime_pd', 'weighted_lifetime_pd', 'cecl_el'])
        
    return df

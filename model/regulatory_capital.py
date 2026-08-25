"""
Basel II/III IRB Regulatory Capital Implementation.

This module provides functions to compute asset correlation, maturity adjustments,
and capital requirements according to the Basel framework.
"""

import logging
import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, Any

logger = logging.getLogger(__name__)

def compute_asset_correlation(pd_val: float, size_adjustment: float = 50.0) -> float:
    r"""
    Compute the Basel IRB asset correlation ($\rho$).
    
    The asset correlation is computed as:
    $$ \rho = 0.12 \times \frac{1 - e^{-50 \times PD}}{1 - e^{-50}} + 0.24 \times \left[ 1 - \frac{1 - e^{-50 \times PD}}{1 - e^{-50}} \right] $$
    
    For SMEs (size_adjustment $S$ in [5, 50]), an adjustment is applied:
    $$ \rho_{adjusted} = \rho - 0.04 \times \left( 1 - \frac{S - 5}{45} \right) $$
    
    Args:
        pd_val (float): Probability of default (PD).
        size_adjustment (float): Annual revenue $S$ in millions. Default is 50.0 (no SME adjustment).
        
    Returns:
        float: The asset correlation $\rho$.
    """
    # Clip PD per Basel floor
    pd_val = max(0.0003, min(float(pd_val), 1.0))
    
    factor = (1.0 - np.exp(-50.0 * pd_val)) / (1.0 - np.exp(-50.0))
    rho = 0.12 * factor + 0.24 * (1.0 - factor)
    
    # SME Size adjustment
    S = max(5.0, min(float(size_adjustment), 50.0))
    rho_adjusted = rho - 0.04 * (1.0 - (S - 5.0) / 45.0)
    
    return float(rho_adjusted)

def compute_capital_requirement(
    pd_val: float,
    lgd: float = 0.45,
    maturity: float = 2.5,
    size_adjustment: float = 50.0
) -> Dict[str, float]:
    r"""
    Compute the Basel IRB capital requirement.
    
    The maturity adjustment is given by:
    $$ b = (0.11852 - 0.05478 \times \ln(PD))^2 $$
    $$ MA = \frac{1 + (M - 2.5) \times b}{1 - 1.5 \times b} $$
    
    The capital requirement ($K$) is:
    $$ K = \left[ \Phi\left( \frac{\Phi^{-1}(PD) + \sqrt{\rho} \times \Phi^{-1}(0.999)}{\sqrt{1 - \rho}} \right) - PD \right] \times LGD \times MA $$
    
    RWA density = $K \times 12.5$
    
    Args:
        pd_val (float): Probability of default.
        lgd (float): Loss given default. Default 0.45.
        maturity (float): Maturity in years. Default 2.5.
        size_adjustment (float): Size adjustment for SMEs. Default 50.0.
        
    Returns:
        dict: A dictionary containing 'K', 'RWA_density', 'rho', 'maturity_adjustment', 'b_coefficient', and 'capital_buffer'.
    """
    pd_val_adj = max(0.0003, min(float(pd_val), 1.0))
    
    b = (0.11852 - 0.05478 * np.log(pd_val_adj)) ** 2
    MA = (1.0 + (maturity - 2.5) * b) / (1.0 - 1.5 * b)
    
    rho = compute_asset_correlation(pd_val_adj, size_adjustment)
    
    # K computation
    z_pd = norm.ppf(pd_val_adj)
    z_999 = norm.ppf(0.999)
    
    x = (z_pd + np.sqrt(rho) * z_999) / np.sqrt(1.0 - rho)
    prob = norm.cdf(x)
    
    K = (prob - pd_val_adj) * lgd * MA
    # Convert numpy types to standard python floats for JSON serialization
    K = float(max(0.0, K))
    
    RWA_density = K * 12.5
    
    return {
        'K': K,
        'RWA_density': RWA_density,
        'rho': rho,
        'maturity_adjustment': float(MA),
        'b_coefficient': float(b),
        'capital_buffer': K
    }

def compute_capital_from_merton(merton_results: Dict[str, Any], lgd: float = 0.45, maturity: float = 2.5) -> Dict[str, Any]:
    r"""
    Compute regulatory capital from Merton model results.
    
    Extracts the PD (risk-neutral) from merton_results to compute capital requirements.
    
    Args:
        merton_results (dict): Output from run_single_firm.
        lgd (float): Loss given default. Default 0.45.
        maturity (float): Maturity in years. Default 2.5.
        
    Returns:
        dict: Dictionary containing 'spot_capital' and 'term_capital'.
    """
    pd_spot = float(merton_results.get("PD_rn", 0.0))
    
    spot_capital_res = compute_capital_requirement(pd_spot, lgd, maturity)
    
    term_capital = {}
    pd_term_structure = merton_results.get("pd_term_structure", {})
    
    for horizon, pd_h in pd_term_structure.items():
        cap_req = compute_capital_requirement(float(pd_h), lgd, float(horizon))
        term_capital[float(horizon)] = float(cap_req['K'])
        
    return {
        'spot_capital': spot_capital_res,
        'term_capital': term_capital
    }

def compute_panel_capital(panel_results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    r"""
    Compute capital requirements for a panel of firms.
    
    Args:
        panel_results (dict[str, dict]): A dictionary mapping ticker to Merton model results.
        
    Returns:
        pd.DataFrame: DataFrame containing ticker, PD, rho, K, RWA_density.
    """
    records = []
    
    for ticker, merton_res in panel_results.items():
        pd_rn = float(merton_res.get("PD_rn", 0.0))
        cap_req = compute_capital_requirement(pd_rn)
        
        records.append({
            "ticker": str(ticker),
            "PD": pd_rn,
            "rho": float(cap_req['rho']),
            "K": float(cap_req['K']),
            "RWA_density": float(cap_req['RWA_density'])
        })
        
    df = pd.DataFrame(records)
    return df

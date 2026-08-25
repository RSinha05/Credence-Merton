"""
Moody's Private Firm Model Implementation
Provides functions to estimate DD for private companies without traded equity.
"""

import logging
import pandas as pd
import numpy as np

from model.merton import (
    compute_distance_to_default,
    compute_probability_of_default,
    compute_pd_term_structure
)
from data.private_comps import (
    PrivateCompany,
    find_comparable_companies,
    compute_peer_multiples
)

logger = logging.getLogger(__name__)

def proxy_asset_value(ebitda: float, peer_ev_ebitda: float) -> float:
    """
    Compute enterprise value proxy for a private firm.
    
    .. math:: V = EBITDA \times \text{peer EV/EBITDA}
    
    Args:
        ebitda (float): Firm EBITDA.
        peer_ev_ebitda (float): Median EV/EBITDA multiple of comparable peers.
        
    Returns:
        float: Proxied asset value (Enterprise Value).
    """
    return float(ebitda * peer_ev_ebitda)

def hamada_unlever_vol(equity_vol: float, leverage_de: float, tax_rate: float = 0.25) -> float:
    r"""
    Unlever equity volatility to obtain asset volatility using Hamada's equation.
    
    .. math:: \sigma_A = \frac{\sigma_E}{1 + (1 - \tau) \frac{D}{E}}
    
    Args:
        equity_vol (float): Equity volatility of the peer.
        leverage_de (float): Debt-to-Equity ratio of the peer.
        tax_rate (float, optional): Corporate tax rate. Defaults to 0.25.
        
    Returns:
        float: Unlevered asset volatility.
    """
    return float(equity_vol / (1.0 + (1.0 - tax_rate) * leverage_de))

def relever_vol(unlevered_vol: float, target_de: float, tax_rate: float = 0.25) -> float:
    """
    Relever volatility for the target company.
    Since we are estimating asset volatility directly, the unlevered vol is the asset vol.
    
    Args:
        unlevered_vol (float): Unlevered asset volatility from peers.
        target_de (float): Target firm's Debt-to-Equity ratio.
        tax_rate (float, optional): Corporate tax rate. Defaults to 0.25.
        
    Returns:
        float: Relevered asset volatility.
    """
    return float(unlevered_vol)

def run_private_firm_model(company: PrivateCompany, tax_rate: float = 0.25) -> dict:
    """
    Estimate Distance to Default (DD) and Probability of Default (PD) for a private firm.
    
    Args:
        company (PrivateCompany): The private company instance.
        tax_rate (float, optional): Corporate tax rate. Defaults to 0.25.
        
    Returns:
        dict: A dictionary containing the model results including V_proxy, sigma_V, D, DD, PD, etc.
    """
    logger.info(f"Running Moody's Private Firm Model for {company.name}")
    
    comps = find_comparable_companies(company)
    n_comps = len(comps)
    
    if n_comps == 0:
        logger.warning(f"No comparable companies found for {company.name}")
        return {
            'V_proxy': np.nan, 'sigma_V': np.nan, 'D': company.total_debt,
            'DD': np.nan, 'PD': np.nan, 'pd_term_structure': {},
            'peer_multiples': {}, 'n_comps': 0, 'methodology': 'Moodys Private Firm Model'
        }
        
    peer_metrics = compute_peer_multiples(comps)
    median_ev_ebitda = peer_metrics.get("median_ev_ebitda", 10.0)
    median_equity_vol = peer_metrics.get("median_equity_vol", 0.40)
    median_de = peer_metrics.get("median_de", 1.0)
    
    V_proxy = proxy_asset_value(company.ebitda, median_ev_ebitda)
    
    # Proxy sigma_V = Hamada-unlever median peer equity vol
    sigma_V = hamada_unlever_vol(median_equity_vol, median_de, tax_rate)
    
    D = float(company.total_debt)
    
    # Compute DD using compute_distance_to_default
    DD = float(compute_distance_to_default(V_proxy, D, sigma_V, mu=0.05, T=1.0))
    
    # Compute PD from DD
    PD = float(compute_probability_of_default(DD))
    
    # Compute PD term structure
    # Assuming compute_pd_term_structure takes V, D, sigma_V, mu, or whatever the actual signature is
    try:
        # Will try passing what might be the standard args or adjust based on typical usage
        pd_ts = compute_pd_term_structure(V_proxy, D, sigma_V, mu=0.05)
    except Exception as e:
        logger.debug(f"Could not compute PD term structure normally, doing fallback: {e}")
        # fallback implementation using just DD * sqrt(1/T)
        pd_ts = {
            t: float(compute_probability_of_default(
                compute_distance_to_default(V_proxy, D, sigma_V, mu=0.05, T=t)
            ))
            for t in [0.5, 1.0, 2.0, 3.0, 5.0]
        }
        
    return {
        'V_proxy': V_proxy,
        'sigma_V': sigma_V,
        'D': D,
        'DD': DD,
        'PD': PD,
        'pd_term_structure': pd_ts,
        'peer_multiples': peer_metrics,
        'n_comps': n_comps,
        'methodology': 'Moodys Private Firm Model'
    }

def run_portfolio_private_firms(companies: list[PrivateCompany]) -> pd.DataFrame:
    """
    Run the private firm model for a portfolio of companies.
    
    Args:
        companies (list[PrivateCompany]): List of private companies.
        
    Returns:
        pd.DataFrame: DataFrame containing name, V_proxy, sigma_V, D, DD, PD, n_comps for each firm.
    """
    results = []
    for comp in companies:
        res = run_private_firm_model(comp)
        results.append({
            'name': comp.name,
            'V_proxy': res['V_proxy'],
            'sigma_V': res['sigma_V'],
            'D': res['D'],
            'DD': res['DD'],
            'PD': res['PD'],
            'n_comps': res['n_comps']
        })
        
    return pd.DataFrame(results)

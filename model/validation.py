import logging
from typing import Tuple, List, Any
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)

def compute_spearman_correlation(
    results: pd.DataFrame
) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation between risk-neutral PD and rating ordinal.

    Higher ordinal implies worse rating and should be correlated with a higher PD.

    Args:
        results: DataFrame containing 'ticker', 'pd_risk_neutral', and 'ordinal' columns.

    Returns:
        Tuple of (correlation, p_value).
    """
    pd_col = 'pd_risk_neutral' if 'pd_risk_neutral' in results.columns else 'PD_rn'
    
    if pd_col not in results.columns or 'ordinal' not in results.columns:
        logger.error(f"DataFrame must contain '{pd_col}' and 'ordinal' columns.")
        raise ValueError(f"DataFrame must contain '{pd_col}' and 'ordinal' columns.")

    valid_data = results[[pd_col, 'ordinal']].dropna()
    if len(valid_data) < 2:
        return np.nan, np.nan
        
    correlation, p_value = spearmanr(valid_data[pd_col], valid_data['ordinal'])
    return float(correlation), float(p_value)

def build_validation_table(
    results: List[dict],
    firm_panel: list
) -> pd.DataFrame:
    """
    Build a summary DataFrame mapping firm validation results.

    Columns included: ticker, name, sp_rating, ordinal, sigma_V, DD, PD_rn, PD_rw.
    The resulting DataFrame is sorted by 'ordinal' ascending.

    Args:
        results: List of per-firm result dicts from run_single_firm.
                 Each dict should ideally have a 'ticker' or align with firm_panel.
        firm_panel: List of objects or dicts from config with firm info.
                    Should contain 'ticker', 'name', 'sp_rating', 'ordinal'.

    Returns:
        A sorted pd.DataFrame with the summary data.
    """
    rows = []
    
    for res, firm in zip(results, firm_panel):
        if isinstance(firm, dict):
            ticker = firm.get('ticker')
            name = firm.get('name')
            sp_rating = firm.get('sp_rating')
            ordinal = firm.get('ordinal')
        else:
            ticker = getattr(firm, 'ticker', None)
            name = getattr(firm, 'name', None)
            sp_rating = getattr(firm, 'sp_rating', None)
            ordinal = getattr(firm, 'ordinal', None)
            
        row = {
            'ticker': res.get('ticker', ticker),
            'name': name,
            'sp_rating': sp_rating,
            'ordinal': ordinal,
            'sigma_V': res.get('sigma_V'),
            'DD': res.get('DD_rw', res.get('DD_rn')),
            'PD_rn': res.get('PD_rn'),
            'PD_rw': res.get('PD_rw')
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty and 'ordinal' in df.columns:
        df = df.sort_values('ordinal', ascending=True).reset_index(drop=True)
    return df

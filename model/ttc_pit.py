"""
Through-the-Cycle (TTC) and Point-in-Time (PIT) Probability of Default calculations.

This module separates TTC PD (based on historical long-run averages for a given rating)
from PIT PD (based on current market-implied values from the Merton model).
"""

import logging
from typing import Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)

LONG_RUN_DEFAULT_RATES = {
    'AAA': 0.0001,
    'AA': 0.0002,
    'A': 0.0006,
    'BBB': 0.0018,
    'BB': 0.0098,
    'B': 0.0446,
    'CCC': 0.1513,
    'D': 1.0
}

def dd_to_rating_bucket(dd: float) -> str:
    """
    Map Distance to Default (DD) to a rating bucket.
    
    Args:
        dd: Distance to default value.
        
    Returns:
        String representing the rating bucket.
    """
    if dd > 5.0:
        return 'AAA'
    elif 4.0 < dd <= 5.0:
        return 'AA'
    elif 3.0 < dd <= 4.0:
        return 'A'
    elif 2.0 < dd <= 3.0:
        return 'BBB'
    elif 1.5 < dd <= 2.0:
        return 'BB'
    elif 1.0 < dd <= 1.5:
        return 'B'
    elif 0.0 <= dd <= 1.0:
        return 'CCC'
    else:
        return 'D'

def compute_ttc_pd(dd: float) -> Dict[str, Any]:
    """
    Compute Through-the-Cycle (TTC) PD based on DD.
    
    Args:
        dd: Distance to default value.
        
    Returns:
        Dictionary with rating_bucket, ttc_pd, and dd.
    """
    rating = dd_to_rating_bucket(dd)
    ttc_pd = LONG_RUN_DEFAULT_RATES.get(rating, 1.0)
    
    logger.debug(f"Mapped DD {dd:.4f} to rating {rating} with TTC PD {ttc_pd}")
    
    return {
        'rating_bucket': rating,
        'ttc_pd': ttc_pd,
        'dd': dd
    }

def compute_pit_pd(merton_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract Point-in-Time (PIT) PD from Merton model results.
    
    Args:
        merton_results: Dictionary of results from the Merton model.
        
    Returns:
        Dictionary with PIT PD and DD values.
    """
    pit_pd_rn = merton_results.get('PD_rn', 0.0)
    pit_pd_rw = merton_results.get('PD_rw', 0.0)
    dd_rn = merton_results.get('DD_rn', 0.0)
    dd_rw = merton_results.get('DD_rw', 0.0)
    
    return {
        'pit_pd_rn': pit_pd_rn,
        'pit_pd_rw': pit_pd_rw,
        'dd_rn': dd_rn,
        'dd_rw': dd_rw
    }

def compute_ttc_pit_comparison(merton_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute both TTC and PIT PD and compare them.
    
    Args:
        merton_results: Dictionary of results from the Merton model.
        
    Returns:
        Dictionary combining TTC and PIT analysis.
    """
    dd_rw = merton_results.get('DD_rw', 0.0)
    
    ttc_info = compute_ttc_pd(dd_rw)
    pit_info = compute_pit_pd(merton_results)
    
    ttc_pd = ttc_info['ttc_pd']
    pit_pd_rw = pit_info['pit_pd_rw']
    
    ratio = pit_pd_rw / ttc_pd if ttc_pd > 0 else float('inf')
    cycle_adjustment = pit_pd_rw - ttc_pd
    
    if ratio > 1.5:
        interpretation = 'procyclical'
    elif ratio < 0.5:
        interpretation = 'countercyclical'
    else:
        interpretation = 'neutral'
        
    return {
        'ttc': ttc_info,
        'pit': pit_info,
        'ratio': ratio,
        'cycle_adjustment': cycle_adjustment,
        'interpretation': interpretation
    }

def compute_panel_ttc_pit(panel_results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Compute TTC vs PIT comparison for a panel of firms.
    
    Args:
        panel_results: Dictionary mapping tickers to their Merton model results.
        
    Returns:
        DataFrame containing the comparison results.
    """
    rows = []
    
    for ticker, results in panel_results.items():
        comp = compute_ttc_pit_comparison(results)
        
        rows.append({
            'ticker': ticker,
            'DD_rw': comp['pit']['dd_rw'],
            'rating_bucket': comp['ttc']['rating_bucket'],
            'TTC_PD': comp['ttc']['ttc_pd'],
            'PIT_PD_rn': comp['pit']['pit_pd_rn'],
            'PIT_PD_rw': comp['pit']['pit_pd_rw'],
            'ratio': comp['ratio'],
            'interpretation': comp['interpretation']
        })
        
    df = pd.DataFrame(rows)
    logger.info(f"Computed TTC/PIT comparison for {len(rows)} firms")
    return df

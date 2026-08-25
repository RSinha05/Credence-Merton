"""
migration.py

Module for building rating migration matrices from distance to default (DD) time series.
Computes rating transition probabilities based on distance to default thresholds.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger(__name__)

RATING_ORDER = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D']

def dd_to_rating(dd: float) -> str:
    """
    Map Distance to Default (DD) to a rating bucket.
    
    Mapping criteria:
    DD > 5.0      -> 'AAA'
    4.0 < DD <= 5.0 -> 'AA'
    3.0 < DD <= 4.0 -> 'A'
    2.0 < DD <= 3.0 -> 'BBB'
    1.5 < DD <= 2.0 -> 'BB'
    1.0 < DD <= 1.5 -> 'B'
    0.0 <= DD <= 1.0 -> 'CCC'
    DD < 0.0      -> 'D'

    Args:
        dd: Distance to default value.

    Returns:
        String representing the rating bucket.
    """
    if pd.isna(dd):
        return 'D'
    if dd > 5.0:
        return 'AAA'
    elif dd > 4.0:
        return 'AA'
    elif dd > 3.0:
        return 'A'
    elif dd > 2.0:
        return 'BBB'
    elif dd > 1.5:
        return 'BB'
    elif dd > 1.0:
        return 'B'
    elif dd >= 0.0:
        return 'CCC'
    else:
        return 'D'

def compute_migration_series(dd_timeseries: pd.Series, freq: str = 'M') -> pd.Series:
    """
    Resample dd_timeseries to given frequency and map each DD to a rating.

    Args:
        dd_timeseries: Pandas Series of distance to default values, indexed by datetime.
        freq: Frequency to resample to (monthly by default).

    Returns:
        Pandas Series of ratings (str) indexed by date.
    """
    logger.debug(f"Computing migration series with frequency: {freq}")
    
    # Resample using the last observation in the period
    resampled_dd = dd_timeseries.resample(freq).last().dropna()
    rating_series = resampled_dd.apply(dd_to_rating)
    return rating_series

def compute_transition_matrix(rating_series: pd.Series) -> pd.DataFrame:
    """
    Compute the transition matrix from a series of ratings.

    Args:
        rating_series: Pandas Series of ratings ordered by time.

    Returns:
        A DataFrame representing the transition matrix with rows as from-ratings
        and columns as to-ratings.
    """
    logger.debug("Computing transition matrix.")
    transitions = pd.DataFrame({
        'from_rating': rating_series.iloc[:-1].values,
        'to_rating': rating_series.iloc[1:].values
    })
    
    # Create empty matrix
    matrix = pd.DataFrame(0.0, index=RATING_ORDER, columns=RATING_ORDER)
    
    if transitions.empty:
        return matrix
        
    counts = pd.crosstab(transitions['from_rating'], transitions['to_rating'])
    
    # Fill in the observed counts
    for r_from in counts.index:
        for r_to in counts.columns:
            if r_from in matrix.index and r_to in matrix.columns:
                matrix.loc[r_from, r_to] = counts.loc[r_from, r_to]
                
    # Normalize rows
    row_sums = matrix.sum(axis=1)
    for idx in matrix.index:
        if row_sums[idx] > 0:
            matrix.loc[idx] = matrix.loc[idx] / row_sums[idx]
            
    # D is an absorbing state
    if row_sums['D'] == 0:
        matrix.loc['D', 'D'] = 1.0
        
    return matrix

def compute_migration_from_merton(merton_results: Dict[str, Any], freq: str = 'M') -> Dict[str, Any]:
    """
    Extract DD timeseries from merton_results and compute migration statistics.

    Args:
        merton_results: Dictionary containing merton outputs, including 'dd_timeseries'.
        freq: Frequency for migration analysis.

    Returns:
        Dictionary with transition matrix, rating history, and summary.
    """
    logger.info("Computing migration from Merton results.")
    
    if 'dd_timeseries' not in merton_results:
        logger.warning("No 'dd_timeseries' found in merton_results.")
        return {}
        
    dd_ts = merton_results['dd_timeseries']
    
    if dd_ts.empty:
        return {}
        
    rating_series = compute_migration_series(dd_ts, freq)
    transition_matrix = compute_transition_matrix(rating_series)
    
    # Calculate downgrades, upgrades, stability
    rating_idx_map = {r: i for i, r in enumerate(RATING_ORDER)}
    
    downgrades = 0
    upgrades = 0
    
    # Ensure indices exist before comparison
    if len(rating_series) > 1:
        prev_ratings = rating_series.iloc[:-1].values
        curr_ratings = rating_series.iloc[1:].values
        
        for prev, curr in zip(prev_ratings, curr_ratings):
            prev_idx = rating_idx_map.get(prev, -1)
            curr_idx = rating_idx_map.get(curr, -1)
            
            if prev_idx != -1 and curr_idx != -1:
                if curr_idx > prev_idx:
                    downgrades += 1
                elif curr_idx < prev_idx:
                    upgrades += 1
                    
    stability = np.trace(transition_matrix.values) / len(RATING_ORDER)
    
    # Convert types to native python for serialization
    tm_dict = transition_matrix.to_dict(orient='index')
    native_tm_dict = {
        k: {k2: float(v2) for k2, v2 in v.items()}
        for k, v in tm_dict.items()
    }
    
    history_dict = {
        k.strftime('%Y-%m-%d') if hasattr(k, 'strftime') else str(k): str(v)
        for k, v in rating_series.to_dict().items()
    }
    
    return {
        'transition_matrix': native_tm_dict,
        'rating_history': history_dict,
        'summary': {
            'downgrades': int(downgrades),
            'upgrades': int(upgrades),
            'stability': float(stability)
        }
    }

def compute_panel_migration(panel_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Pool all firms' rating transitions into one large matrix (aggregate).

    Args:
        panel_results: Dictionary mapping firm IDs to their merton results dicts.

    Returns:
        Dictionary containing the aggregate transition matrix and per-firm summaries.
    """
    logger.info("Computing panel migration matrix.")
    
    aggregate_counts = pd.DataFrame(0.0, index=RATING_ORDER, columns=RATING_ORDER)
    firm_summaries = {}
    
    for firm_id, results in panel_results.items():
        if 'dd_timeseries' not in results:
            continue
            
        dd_ts = results['dd_timeseries']
        if dd_ts.empty:
            continue
            
        rating_series = compute_migration_series(dd_ts, freq='M')
        
        # Calculate transitions for this firm
        if len(rating_series) > 1:
            transitions = pd.DataFrame({
                'from_rating': rating_series.iloc[:-1].values,
                'to_rating': rating_series.iloc[1:].values
            })
            counts = pd.crosstab(transitions['from_rating'], transitions['to_rating'])
            
            for r_from in counts.index:
                for r_to in counts.columns:
                    if r_from in aggregate_counts.index and r_to in aggregate_counts.columns:
                        aggregate_counts.loc[r_from, r_to] += counts.loc[r_from, r_to]
                        
        mig_res = compute_migration_from_merton(results, freq='M')
        if 'summary' in mig_res:
            firm_summaries[firm_id] = mig_res['summary']
            
    # Normalize rows
    aggregate_matrix = pd.DataFrame(0.0, index=RATING_ORDER, columns=RATING_ORDER)
    row_sums = aggregate_counts.sum(axis=1)
    
    for idx in aggregate_matrix.index:
        if row_sums[idx] > 0:
            aggregate_matrix.loc[idx] = aggregate_counts.loc[idx] / row_sums[idx]
            
    # D is an absorbing state
    if row_sums['D'] == 0:
        aggregate_matrix.loc['D', 'D'] = 1.0
        
    tm_dict = aggregate_matrix.to_dict(orient='index')
    native_tm_dict = {
        k: {k2: float(v2) for k2, v2 in v.items()}
        for k, v in tm_dict.items()
    }
    
    return {
        'aggregate_matrix': native_tm_dict,
        'firm_summaries': firm_summaries
    }

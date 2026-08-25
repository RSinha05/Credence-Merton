"""
Portfolio risk module for single-factor Gaussian-copula (Vasicek) credit VaR.
"""
import logging
from typing import Dict, Any
import numpy as np
import pandas as pd
from scipy.stats import norm

logger = logging.getLogger(__name__)

def compute_asset_correlation_from_returns(asset_series_dict: Dict[str, pd.Series]) -> pd.DataFrame:
    """
    Compute pairwise correlations of log returns of asset series.

    Parameters
    ----------
    asset_series_dict : Dict[str, pd.Series]
        Dictionary mapping ticker to asset value series (V).

    Returns
    -------
    pd.DataFrame
        Correlation matrix of the asset log returns.
    """
    logger.info("Computing asset correlation from returns.")
    df = pd.DataFrame(asset_series_dict)
    returns = np.log(df / df.shift(1)).dropna()
    return returns.corr()

def vasicek_portfolio_loss(
    pds: np.ndarray,
    lgds: np.ndarray,
    exposures: np.ndarray,
    rho: float,
    confidence: float = 0.999,
    n_simulations: int = 100000
) -> Dict[str, Any]:
    """
    Compute Portfolio VaR and Expected Shortfall using single-factor Gaussian copula Monte Carlo.

    Parameters
    ----------
    pds : np.ndarray
        Array of Probabilities of Default for each obligor.
    lgds : np.ndarray
        Array of Loss Given Default for each obligor.
    exposures : np.ndarray
        Array of Exposure at Default (EAD) for each obligor.
    rho : float
        Uniform asset correlation.
    confidence : float, optional
        Confidence level for VaR and CVaR, by default 0.999
    n_simulations : int, optional
        Number of Monte Carlo simulations, by default 100000

    Returns
    -------
    Dict[str, Any]
        Dictionary containing VaR, CVaR, expected_loss, unexpected_loss, and loss percentiles.
    """
    logger.info(f"Running Vasicek portfolio loss MC with {n_simulations} simulations.")
    n_obligors = len(pds)
    
    # Clip PDs to avoid infinity with probit
    pds = np.clip(pds, 1e-8, 1 - 1e-8)
    default_thresholds = norm.ppf(pds)
    
    # Draw systematic factor Z ~ N(0,1)
    Z = np.random.standard_normal(n_simulations)
    
    # Pre-calculate constants
    sqrt_rho = np.sqrt(rho)
    sqrt_one_minus_rho = np.sqrt(1 - rho)
    
    # Using a fast vectorized approach
    Z_component = sqrt_rho * Z[:, np.newaxis]
    
    # epsilon ~ N(0,1) for each obligor in each simulation
    epsilon = np.random.standard_normal((n_simulations, n_obligors))
    
    # Asset returns X_i
    X = Z_component + sqrt_one_minus_rho * epsilon
    
    # Default indicator
    defaults = X < default_thresholds
    
    # Calculate losses
    losses = defaults * (lgds * exposures)
    portfolio_losses = losses.sum(axis=1)
    
    # Calculate metrics
    expected_loss = float(np.mean(portfolio_losses))
    var = float(np.percentile(portfolio_losses, confidence * 100))
    
    # Expected Shortfall (CVaR)
    tail_losses = portfolio_losses[portfolio_losses >= var]
    cvar = float(np.mean(tail_losses)) if len(tail_losses) > 0 else var
    
    unexpected_loss = var - expected_loss
    
    percentiles = {
        '50th': float(np.percentile(portfolio_losses, 50)),
        '75th': float(np.percentile(portfolio_losses, 75)),
        '90th': float(np.percentile(portfolio_losses, 90)),
        '95th': float(np.percentile(portfolio_losses, 95)),
        '99th': float(np.percentile(portfolio_losses, 99)),
        '99.9th': float(np.percentile(portfolio_losses, 99.9)),
    }
    
    return {
        'VaR': var,
        'CVaR': cvar,
        'expected_loss': expected_loss,
        'unexpected_loss': unexpected_loss,
        'loss_distribution_percentiles': percentiles
    }

def vasicek_analytical_var(pd_val: float, lgd: float, rho: float, confidence: float = 0.999) -> float:
    """
    Compute analytical Vasicek portfolio VaR (homogeneous portfolio approximation).

    Formula:
    $$ VaR = LGD \\times \\Phi\\left(\\frac{\\Phi^{-1}(PD) + \\sqrt{\\rho} \\times \\Phi^{-1}(confidence)}{\\sqrt{1 - \\rho}}\\right) $$

    Parameters
    ----------
    pd_val : float
        Probability of Default.
    lgd : float
        Loss Given Default.
    rho : float
        Asset correlation.
    confidence : float, optional
        Confidence level, by default 0.999.

    Returns
    -------
    float
        Analytical VaR per unit of exposure.
    """
    logger.info("Computing analytical Vasicek VaR.")
    pd_val = min(max(pd_val, 1e-8), 1 - 1e-8)
    num = norm.ppf(pd_val) + np.sqrt(rho) * norm.ppf(confidence)
    den = np.sqrt(1 - rho)
    return float(lgd * norm.cdf(num / den))

def compute_portfolio_risk(panel_results: Dict[str, Dict[str, Any]], lgd: float = 0.45, confidence: float = 0.999) -> Dict[str, Any]:
    """
    Compute portfolio risk metrics from panel Merton results.

    Parameters
    ----------
    panel_results : Dict[str, Dict[str, Any]]
        Dictionary mapping ticker to merton_results.
    lgd : float, optional
        Loss Given Default, by default 0.45
    confidence : float, optional
        Confidence level, by default 0.999

    Returns
    -------
    Dict[str, Any]
        Dictionary with var, cvar, expected_loss, correlation_matrix, concentration.
    """
    logger.info("Computing portfolio risk from panel results.")
    tickers = list(panel_results.keys())
    
    if not tickers:
        logger.warning("Empty panel results.")
        return {}
        
    pds = []
    exposures = []
    asset_series_dict = {}
    
    for ticker, res in panel_results.items():
        pd_val = res.get('PD_rw', res.get('PD_rn', 0.0))
        # Use D if available, otherwise V_current or 1.0
        exp = res.get('D', res.get('V_current', 1.0))
        
        pds.append(pd_val)
        exposures.append(exp)
        
        if 'asset_series' in res:
            asset_series_dict[ticker] = res['asset_series']
            
    pds = np.array(pds)
    exposures = np.array(exposures)
    lgds = np.ones_like(pds) * lgd
    
    corr_df = None
    rho = 0.0
    if len(asset_series_dict) > 1:
        corr_df = compute_asset_correlation_from_returns(asset_series_dict)
        # Average off-diagonal correlation
        mask = ~np.eye(corr_df.shape[0], dtype=bool)
        rho = corr_df.values[mask].mean()
        if np.isnan(rho):
            rho = 0.0
    else:
        rho = 0.2
        if len(asset_series_dict) == 1:
            df = pd.DataFrame(asset_series_dict)
            corr_df = pd.DataFrame(1.0, index=df.columns, columns=df.columns)
            
    mc_results = vasicek_portfolio_loss(pds, lgds, exposures, rho, confidence=confidence)
    
    # Concentration metrics
    total_exposure = np.sum(exposures)
    if total_exposure > 0:
        exposure_shares = exposures / total_exposure
        hhi = float(np.sum(exposure_shares ** 2))
        top_5_share = float(np.sum(np.sort(exposure_shares)[-5:]))
    else:
        hhi = 0.0
        top_5_share = 0.0
        
    return {
        'var': mc_results['VaR'],
        'cvar': mc_results['CVaR'],
        'expected_loss': mc_results['expected_loss'],
        'correlation_matrix': corr_df.to_dict() if corr_df is not None else None,
        'concentration': {
            'HHI': hhi,
            'top_5_exposure_share': top_5_share
        }
    }

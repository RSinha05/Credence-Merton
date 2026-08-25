import logging
from typing import Tuple, List, Dict
import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import brentq
from model.calibration import DDCalibrator

# Initialize calibrator once globally for performance
_CALIBRATOR = DDCalibrator()
_CALIBRATOR.fit_synthetic()

logger = logging.getLogger(__name__)

def _merton_equity_equation(V: float, E: float, D: float, r: float, T: float, sigma_V: float) -> float:
    r"""
    Helper function for the Merton model equity equation used for root finding.

    The Merton model values equity as a European call option on the firm's assets.
    Equation:
    $$E = V \Phi(d_1) - D e^{-rT} \Phi(d_2)$$
    where:
    $$d_1 = \frac{\ln(V/D) + (r + 0.5 \sigma_V^2)T}{\sigma_V \sqrt{T}}$$
    $$d_2 = d_1 - \sigma_V \sqrt{T}$$

    Args:
        V: Current asset value of the firm
        E: Current equity value (market cap) of the firm
        D: Default point (debt face value)
        r: Risk-free rate (annualized, continuous)
        T: Time horizon to default (years)
        sigma_V: Volatility of the firm's asset value (annualized)

    Returns:
        The residual: V * N(d1) - D * exp(-r*T) * N(d2) - E
    """
    if V <= 0:
        return -E

    d1 = (np.log(V / D) + (r + 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))
    d2 = d1 - sigma_V * np.sqrt(T)

    E_calc = V * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)
    return E_calc - E

def solve_merton_vk(
    equity_series: pd.Series,
    D: float | pd.Series,
    r: float,
    T: float = 1.0,
    max_iter: int = 50,
    tol: float = 1e-6
) -> Tuple[pd.Series, float, float, int]:
    r"""
    Core Vasicek-Kealhofer (VK) Iterative Solver for Asset Value and Volatility.

    This algorithm solves for the unobservable asset value $V_t$ and asset volatility $\sigma_V$ 
    using a time series of equity values $E_t$.

    Algorithm steps:
    1. Compute initial equity volatility $\sigma_E$.
    2. Seed initial $\sigma_V = \sigma_E \frac{E}{E + D}$.
    3. Iterate until convergence:
       a. For each day, solve for $V_t$ using Brent's method on the Merton equity equation.
       b. Recompute $\sigma_V$ from the standard deviation of log returns of the new $V_t$ series.
       c. Check if $|\sigma_V^{new} - \sigma_V| < tol$.

    Args:
        equity_series: Daily market cap series (indexed by date).
        D: Default point (e.g., STD + 0.5 * LTD).
        r: Risk-free rate (annualized, continuous).
        T: Time horizon in years (default 1.0).
        max_iter: Maximum number of iterations (default 50).
        tol: Convergence tolerance for asset volatility (default 1e-6).

    Returns:
        Tuple containing:
        - asset_value_series (pd.Series): The implied daily asset values.
        - sigma_V_final (float): The final implied asset volatility.
        - sigma_V_history_last (float): The asset volatility from the previous iteration.
        - n_iterations (int): The number of iterations taken to converge.
    """
    if len(equity_series) < 2:
        logger.error("Equity series must have at least 2 data points.")
        raise ValueError("Equity series must have at least 2 data points.")

    # 1. Compute sigma_E from the equity series log returns (annualized)
    log_returns_E = np.log(equity_series / equity_series.shift(1)).dropna()
    sigma_E = log_returns_E.std(ddof=1) * np.sqrt(252)

    # 2. Seed: sigma_V
    E_latest = equity_series.iloc[-1]
    sigma_V = sigma_E * E_latest / (E_latest + D)

    asset_series = pd.Series(index=equity_series.index, dtype=float)
    sigma_V_prev = 0.0

    # Align D with equity_series if D is a pandas Series
    if isinstance(D, pd.Series):
        D_aligned = D.reindex(equity_series.index, method='ffill').bfill().values
    else:
        D_aligned = float(D)

    # Initialize V array for vectorized Newton-Raphson
    E = equity_series.values
    V = E + D_aligned
    D = D_aligned  # Override D with the aligned array or float for the loop
    
    for i in range(max_iter):
        sigma_V_prev = sigma_V
        
        # a. Solve for V_t using vectorized Newton-Raphson
        for _ in range(10): # inner Newton iterations
            d1 = (np.log(V / D) + (r + 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))
            d2 = d1 - sigma_V * np.sqrt(T)
            
            BS_Call = V * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)
            error = BS_Call - E
            
            # Derivative of call with respect to V is N(d1)
            dV = error / norm.cdf(d1)
            V = V - dV
            
            if np.max(np.abs(error)) < 1e-4:
                break
                
        # Floor V to E to prevent impossible states
        V = np.maximum(V, E + 1e-4)
        asset_series[:] = V
        
        # b. Compute log returns of the V_t series
        log_returns_V = np.log(asset_series / asset_series.shift(1)).dropna()
        
        # c. Recompute sigma_V_new
        sigma_V_new = log_returns_V.std(ddof=1) * np.sqrt(252)
        
        # d. Converged?
        if abs(sigma_V_new - sigma_V) < tol:
            return asset_series, sigma_V_new, sigma_V, i + 1
            
        sigma_V = sigma_V_new
        
    logger.warning("Vasicek-Kealhofer Iterative Solver did not converge within the maximum number of iterations.")
    return asset_series, sigma_V, sigma_V_prev, max_iter

def compute_distance_to_default(
    V: float,
    D: float,
    sigma_V: float,
    mu: float,
    T: float = 1.0
) -> float:
    r"""
    Computes the Distance-to-Default (DD).

    Formula:
    $$DD = \frac{\ln(V/D) + (\mu - 0.5 \sigma_V^2)T}{\sigma_V \sqrt{T}}$$

    Args:
        V: Current asset value.
        D: Default point.
        sigma_V: Asset volatility.
        mu: Drift (r for risk-neutral, historical mean for real-world).
        T: Time horizon in years (default 1.0).

    Returns:
        The Distance-to-Default (float).
    """
    return (np.log(V / D) + (mu - 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))

def compute_probability_of_default(DD: float) -> float:
    r"""
    Computes the Probability of Default (PD) from Distance-to-Default (DD).

    Formula:
    $$PD = \Phi(-DD)$$

    Args:
        DD: Distance-to-Default.

    Returns:
        The Probability of Default (float).
    """
    return norm.cdf(-DD)

def compute_dd_time_series(
    asset_series: pd.Series,
    D: float,
    sigma_V: float,
    mu: float,
    T: float = 1.0
) -> pd.Series:
    """
    Computes Distance-to-Default (DD) for each date in the asset series.

    Args:
        asset_series: Time series of asset values.
        D: Default point.
        sigma_V: Asset volatility.
        mu: Drift.
        T: Time horizon (default 1.0).

    Returns:
        A pd.Series of DD values indexed by date.
    """
    return asset_series.apply(lambda v: compute_distance_to_default(v, D, sigma_V, mu, T))

def compute_pd_term_structure(
    V: float, D: float, sigma_V: float, mu: float,
    horizons: List[float] = [0.5, 1.0, 2.0, 3.0, 5.0]
) -> Dict[float, float]:
    """
    Computes the Probability of Default (PD) term structure at multiple horizons.

    Args:
        V: Current asset value.
        D: Default point.
        sigma_V: Asset volatility.
        mu: Drift.
        horizons: List of time horizons in years.

    Returns:
        A dictionary mapping each horizon to its corresponding PD.
    """
    term_structure = {}
    for t_h in horizons:
        dd = compute_distance_to_default(V, D, sigma_V, mu, t_h)
        pd_val = compute_probability_of_default(dd)
        term_structure[t_h] = pd_val
    return term_structure

def run_single_firm(
    equity_series: pd.Series,
    D: float | pd.Series,
    r: float,
    T: float = 1.0,
    max_iter: int = 50,
    tol: float = 1e-6,
    sentiment_score: float = None
) -> dict:
    """
    Runs the full single-firm pipeline for Merton/KMV model.

    This includes:
    - Running the VK iterative solver to find V series and sigma_V.
    - Computing real-world drift (annualized mean of asset log returns).
    - Computing DD (risk-neutral and real-world).
    - Computing PD (risk-neutral and real-world).
    - Computing DD time series.
    - Computing PD term structure.

    Args:
        equity_series: Daily market cap series.
        D: Default point.
        r: Risk-free rate.
        T: Time horizon.
        max_iter: Max iterations for VK solver.
        tol: Convergence tolerance for VK solver.

    Returns:
        A dictionary containing all results.
    """
    try:
        asset_series, sigma_V, sigma_V_last, n_iter = solve_merton_vk(equity_series, D, r, T, max_iter, tol)
    except Exception as e:
        logger.error(f"VK solver failed: {e}")
        raise

    V_current = asset_series.iloc[-1]
    D_current = D.iloc[-1] if isinstance(D, pd.Series) else D
    
    # NLP Sentiment Adjustment
    if sentiment_score is not None:
        # Scale volatility based on sentiment (-1.0 to +1.0)
        # E.g., highly negative (-1) -> +20% volatility
        # highly positive (+1) -> -10% volatility
        # Linear interpolation
        vol_modifier = -0.15 * sentiment_score + 0.05
        sigma_V = sigma_V * (1.0 + vol_modifier)
        logger.info(f"Applied NLP Sentiment {sentiment_score:.2f} -> Adjusted sigma_V to {sigma_V:.4f}")

    # Real-world drift mu (annualized mean of log returns)
    log_returns_V = np.log(asset_series / asset_series.shift(1)).dropna()
    mu_rw = log_returns_V.mean() * 252

    # DD
    dd_rn = compute_distance_to_default(V_current, D_current, sigma_V, r, T)
    dd_rw = compute_distance_to_default(V_current, D_current, sigma_V, mu_rw, T)

    # PD
    pd_rn = compute_probability_of_default(dd_rn)
    pd_rw = compute_probability_of_default(dd_rw)

    # Time series
    dd_timeseries = compute_dd_time_series(asset_series, D, sigma_V, mu_rw, T)

    # Term structure
    pd_term_structure = compute_pd_term_structure(V_current, D_current, sigma_V, mu_rw)

    try:
        pd_calibrated = _CALIBRATOR.predict(dd_rw)
    except Exception as e:
        print("CALIBRATOR ERROR:", e)
        pd_calibrated = None

    return {
        "asset_series": asset_series,
        "sigma_V": sigma_V,
        "DD_rn": dd_rn,
        "DD_rw": dd_rw,
        "PD_rn": pd_rn,
        "PD_rw": pd_rw,
        "PD_calibrated": float(pd_calibrated) if pd_calibrated is not None else None,
        "dd_timeseries": dd_timeseries,
        "pd_term_structure": pd_term_structure,
        "iterations": n_iter,
        "mu_rw": mu_rw,
        "V_current": V_current,
        "D": float(D_current)
    }

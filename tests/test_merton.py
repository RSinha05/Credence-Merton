import pytest
import pandas as pd
import numpy as np
from model.merton import solve_merton_vk, compute_distance_to_default, compute_probability_of_default

def test_merton_round_trip():
    # Synthetic equity series
    dates = pd.date_range('2023-01-01', periods=252, freq='B')
    # Random walk with slight upward drift
    returns = np.random.normal(0.0005, 0.015, size=252)
    equity = 100 * np.exp(np.cumsum(returns))
    E_series = pd.Series(equity, index=dates)
    
    D = 50.0
    r = 0.05
    
    asset_series, sigma_V, _, n_iter = solve_merton_vk(E_series, D, r, max_iter=50, tol=1e-5)
    
    assert len(asset_series) == 252
    assert sigma_V > 0
    # V should be strictly greater than E
    assert (asset_series > E_series).all()
    
    # Test DD and PD
    dd = compute_distance_to_default(asset_series.iloc[-1], D, sigma_V, r, 1.0)
    pd_val = compute_probability_of_default(dd)
    
    assert dd > 0  # Generally should be positive for a healthy company
    assert 0 <= pd_val <= 1.0

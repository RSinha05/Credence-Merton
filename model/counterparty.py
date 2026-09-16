import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class CounterpartyRiskEngine:
    """
    Computes Counterparty Credit Risk metrics:
    - Potential Future Exposure (PFE)
    - Expected Exposure (EE)
    - Credit Value Adjustment (CVA)
    """
    def __init__(self, n_simulations: int = 10000, seed: int = 42):
        self.n_simulations = n_simulations
        self.seed = seed
        np.random.seed(self.seed)

    def simulate_exposure(self, initial_value: float, volatility: float, horizon_years: float, steps: int = 12) -> np.ndarray:
        """
        Simulate future exposure of a generic derivative using Geometric Brownian Motion.
        Returns array of shape (steps, n_simulations).
        """
        dt = horizon_years / steps
        # Simple GBM without drift for exposure (assuming martingale under risk-neutral measure)
        # S_t = S_0 * exp( -0.5 * sigma^2 * t + sigma * W_t )
        
        paths = np.zeros((steps + 1, self.n_simulations))
        paths[0] = initial_value
        
        for t in range(1, steps + 1):
            z = np.random.standard_normal(self.n_simulations)
            paths[t] = paths[t-1] * np.exp(-0.5 * volatility**2 * dt + volatility * np.sqrt(dt) * z)
            
        return paths

    def calculate_cva(self, 
                      exposure_paths: np.ndarray, 
                      pd_term_structure: np.ndarray, 
                      lgd: float, 
                      risk_free_rate: float,
                      horizon_years: float) -> Dict[str, Any]:
        """
        Calculate Credit Value Adjustment (CVA) and Potential Future Exposure (PFE).
        
        Args:
            exposure_paths: (steps+1, n_simulations) array of exposures
            pd_term_structure: array of cumulative PDs at each step (length = steps)
            lgd: Loss Given Default
            risk_free_rate: Risk-free rate for discounting
            horizon_years: Total time horizon in years
            
        Returns:
            Dict containing CVA, PFE 95%, Expected Exposure profile
        """
        steps = exposure_paths.shape[0] - 1
        dt = horizon_years / steps
        
        # Max(V, 0) for exposure
        positive_exposures = np.maximum(exposure_paths, 0)
        
        # Expected Exposure (mean across simulations at each time step)
        ee = np.mean(positive_exposures, axis=1)[1:] # Exclude t=0
        
        # Potential Future Exposure (95th percentile)
        pfe_95 = np.percentile(positive_exposures, 95, axis=1)[1:]
        
        # Marginal PDs
        # pd_term_structure is cumulative PD. Marginal is PD(t) - PD(t-1)
        pd_padded = np.insert(pd_term_structure, 0, 0.0)
        marginal_pd = np.diff(pd_padded)
        
        cva = 0.0
        for i in range(steps):
            t = (i + 1) * dt
            discount_factor = np.exp(-risk_free_rate * t)
            cva += lgd * ee[i] * marginal_pd[i] * discount_factor
            
        return {
            'cva': cva,
            'expected_exposure': ee.tolist(),
            'pfe_95': pfe_95.tolist(),
            'time_grid': [ (i+1)*dt for i in range(steps) ]
        }

if __name__ == "__main__":
    engine = CounterpartyRiskEngine(n_simulations=5000)
    # Simulate a contract with initial value $1M, 20% volatility, over 5 years, monthly steps (60 steps)
    exposure = engine.simulate_exposure(1_000_000, 0.20, 5.0, 60)
    
    # Fake cumulative PD term structure: rising from 1% to 10% over 5 years
    cum_pd = np.linspace(0.01, 0.10, 60)
    
    res = engine.calculate_cva(exposure, cum_pd, lgd=0.40, risk_free_rate=0.04, horizon_years=5.0)
    print(f"CVA: ${res['cva']:,.2f}")
    print(f"Max PFE 95%: ${max(res['pfe_95']):,.2f}")

"""
Private firm distance-to-default calibration module.

This module refits the DDCalibrator on a leveraged-loan/private-default base rate
instead of the synthetic public-firm-shaped data.

WHY the same DD maps to different Expected Default Frequencies (EDFs) for private vs public firms:
- Selection bias: Private firms are often leveraged buyouts with higher starting leverage.
- Information asymmetry: Less market discipline, less transparent financials, and delayed reporting.
- Size and Diversification: Private firms are often smaller and less diversified than public peers.
- Higher leverage by design: Private Equity sponsors optimize capital structure aggressively.
"""

import logging
import numpy as np
import pandas as pd
from scipy.stats import norm
from model.calibration import DDCalibrator

logger = logging.getLogger(__name__)

def generate_private_calibration_data(n_samples: int = 5000, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic calibration data tailored for private firms/leveraged loans.
    
    Private firms typically exhibit:
    - Compressed DD values (often between 0 and 5).
    - Higher base default rates (~3-5% vs ~1-2% for public).
    - Fatter tails for low DD values.
    
    Args:
        n_samples (int): Number of synthetic samples.
        seed (int): Random seed.
        
    Returns:
        tuple[np.ndarray, np.ndarray]: (dd_values, empirical_default_rates)
    """
    np.random.seed(seed)
    
    # Private firms typically have DD 0-5, not 0-8
    dd_values = np.linspace(0, 5, n_samples)
    
    # Base theoretical default rate using normal CDF (Merton framework)
    base_pd = norm.cdf(-dd_values)
    
    # Fatter tails: more aggressive fat tail factor for low DD values
    # For private markets, the penalty for low DD is steeper.
    fat_tail_factor = 1.0 + 2.0 * np.exp(-1.0 * dd_values)
    
    # Base rate adjustment: higher base default rate (~3-5% vs ~1-2%)
    # Adding a proportional shift to reflect higher structural risk
    private_base_shift = 0.03
    
    empirical_default_rates = base_pd * fat_tail_factor + private_base_shift * np.exp(-0.5 * dd_values)
    
    # Ensure probabilities are bounded [0, 1]
    empirical_default_rates = np.clip(empirical_default_rates, 0.0, 0.9999)
    
    return dd_values, empirical_default_rates


class PrivateDDCalibrator(DDCalibrator):
    """
    DDCalibrator specialized for private firms and leveraged loans.
    """
    
    def fit_synthetic(self, n_samples: int = 5000, seed: int = 42) -> 'PrivateDDCalibrator':
        """
        Override fit_synthetic to use private calibration data.
        """
        logger.info("Fitting PrivateDDCalibrator with synthetic private data...")
        dd_values, observed_pd = generate_private_calibration_data(n_samples=n_samples, seed=seed)
        self.fit(dd_values, observed_pd)
        return self

    def compare_to_public(self, dd_values: np.ndarray) -> pd.DataFrame:
        """
        Compare EDFs between public and private models for given DD values.
        
        Args:
            dd_values (np.ndarray): Array of Distance-to-Default values.
            
        Returns:
            pd.DataFrame: DataFrame containing DD, public EDF, and private EDF.
        """
        public_calibrator = DDCalibrator()
        if hasattr(public_calibrator, 'fit_synthetic'):
            public_calibrator.fit_synthetic()
        else:
            logger.warning("DDCalibrator does not have fit_synthetic, assuming it's pre-fit or doesn't require it.")
            
        public_edf = public_calibrator.predict(dd_values)
        private_edf = self.predict(dd_values)
        
        df = pd.DataFrame({
            'DD': dd_values,
            'Public_EDF': public_edf,
            'Private_EDF': private_edf,
            'Spread': private_edf - public_edf
        })
        return df


def get_private_calibrator() -> PrivateDDCalibrator:
    """
    Factory function that returns a pre-fitted PrivateDDCalibrator.
    
    Returns:
        PrivateDDCalibrator: Pre-fitted calibrator.
    """
    calibrator = PrivateDDCalibrator()
    calibrator.fit_synthetic()
    return calibrator

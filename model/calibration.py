import logging
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from scipy.stats import norm
from typing import Optional, Tuple, Dict, Union
import json
import os

logger = logging.getLogger(__name__)

def generate_synthetic_calibration_data(
    n_samples: int = 5000,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """Generates synthetic calibration dataset mapping Distance-to-Default (DD) 
    to empirical Expected Default Frequencies (EDF).
    
    Since we don't have access to proprietary default databases (e.g., Moody's KMV),
    we generate a realistic synthetic dataset. Theoretical N(-DD) understates
    default rates due to fat tails in asset returns and model assumptions.
    We introduce a fat-tail adjustment to simulate real-world default probabilities.
    
    Args:
        n_samples (int): Number of synthetic samples to generate.
        seed (int): Random seed for reproducibility.
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: (dd_values, empirical_default_rates)
    """
    np.random.seed(seed)
    
    # Generate DD values (mostly positive, some negative indicating default)
    # Using a mix of uniforms and normals to get a good spread
    dd_values = np.random.uniform(-1, 8, n_samples)
    
    # Base theoretical probability
    base_pd = norm.cdf(-dd_values)
    
    # Fat-tail adjustment: default rates are higher than normal distribution implies,
    # particularly for lower DD values.
    # Factor is larger when DD is smaller (closer to default)
    fat_tail_factor = np.where(dd_values < 3, 1 + 2 * np.exp(-dd_values), 1 + 0.5 * np.exp(-dd_values/2))
    
    adjusted_pd = base_pd * fat_tail_factor
    
    # Add noise
    noise = np.random.normal(0, 0.001, n_samples)
    empirical_pd = adjusted_pd + noise
    
    # Clip to valid probability bounds
    empirical_pd = np.clip(empirical_pd, 0.0, 1.0)
    
    return dd_values, empirical_pd


class DDCalibrator:
    """Maps Distance-to-Default to calibrated Expected Default Frequency (EDF)
    using Isotonic Regression.
    
    Why calibration is needed:
    Theoretical models often assume asset returns are log-normally distributed.
    In reality, returns have fat tails and extreme events occur more frequently 
    than a normal distribution predicts. Thus, N(-DD) heavily understates actual 
    default probability for low and moderate DD values.
    
    Why Isotonic Regression:
    Isotonic regression fits a free-form, non-decreasing function to the data. 
    It guarantees monotonicity (lower DD ALWAYS means higher or equal EDF) 
    without imposing a rigid parametric shape, making it ideal for mapping 
    theoretical risk measures to empirical observations, similar in spirit to 
    Moody's proprietary EDF mappings.
    """
    
    def __init__(self):
        # We model EDF as a non-decreasing function of -DD
        self.model = IsotonicRegression(y_min=0.0, y_max=1.0, increasing=True, out_of_bounds='clip')
        self.is_fitted = False
        self._dd_range: Optional[Tuple[float, float]] = None

    def fit(self, dd_values: np.ndarray, observed_default_rates: np.ndarray) -> 'DDCalibrator':
        """Fits isotonic regression on -DD to observed default rates.
        
        Args:
            dd_values: Array of Distance-to-Default values.
            observed_default_rates: Array of empirical default probabilities.
            
        Returns:
            self
        """
        # Negate DD because EDF should increase as DD decreases
        neg_dd = -np.asarray(dd_values)
        self.model.fit(neg_dd, observed_default_rates)
        
        self._dd_range = (float(np.min(dd_values)), float(np.max(dd_values)))
        self.is_fitted = True
        
        logger.info(f"Calibrator fitted on {len(dd_values)} samples. DD range: {self._dd_range}")
        return self

    def fit_synthetic(self, n_samples: int = 5000) -> 'DDCalibrator':
        """Convenience method to fit on synthetic data."""
        dd, edf = generate_synthetic_calibration_data(n_samples=n_samples)
        return self.fit(dd, edf)

    def predict(self, dd: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Predict calibrated EDF for given DD value(s)."""
        if not self.is_fitted:
            raise RuntimeError("DDCalibrator is not fitted yet.")
            
        dd_arr = np.asarray(dd)
        neg_dd = -dd_arr
        
        preds = self.model.predict(if_else(np.isscalar(dd), [neg_dd], neg_dd))
        
        if np.isscalar(dd):
            return float(preds[0])
        return preds

    def predict_vs_normal(self, dd: Union[float, np.ndarray]) -> Dict:
        """Compares calibrated EDF vs theoretical N(-DD)."""
        calibrated = self.predict(dd)
        normal_edf = norm.cdf(-np.asarray(dd))
        
        if np.isscalar(dd):
            normal_edf = float(normal_edf)
            ratio = calibrated / normal_edf if normal_edf > 0 else 1.0
        else:
            ratio = np.divide(calibrated, normal_edf, out=np.ones_like(calibrated), where=normal_edf!=0)
            
        return {
            'calibrated_edf': calibrated,
            'normal_edf': normal_edf,
            'ratio': ratio
        }

    def save(self, filepath: str) -> None:
        """Saves calibration grid to JSON."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before saving.")
            
        grid = np.linspace(-2, 10, 1000)
        preds = self.predict(grid)
        
        data = {
            'dd_grid': grid.tolist(),
            'edf_grid': preds.tolist(),
            'dd_range': self._dd_range
        }
        
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f)
            
        logger.info(f"Calibration saved to {filepath}")

    def load(self, filepath: str) -> 'DDCalibrator':
        """Loads calibration from JSON and refits."""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        dd_grid = np.array(data['dd_grid'])
        edf_grid = np.array(data['edf_grid'])
        
        self.fit(dd_grid, edf_grid)
        self._dd_range = tuple(data.get('dd_range', (dd_grid.min(), dd_grid.max())))
        
        logger.info(f"Calibration loaded from {filepath}")
        return self

    def calibration_report(self, dd_grid: Optional[np.ndarray] = None) -> pd.DataFrame:
        """Generates a report comparing calibrated vs theoretical EDFs."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted to generate report.")
            
        if dd_grid is None:
            dd_grid = np.arange(-1.0, 8.5, 0.5)
            
        results = self.predict_vs_normal(dd_grid)
        
        df = pd.DataFrame({
            'Distance_to_Default': dd_grid,
            'Theoretical_N(-DD)': results['normal_edf'],
            'Calibrated_EDF': results['calibrated_edf'],
            'Adjustment_Ratio': results['ratio']
        })
        
        return df

def if_else(condition, true_val, false_val):
    return true_val if condition else false_val

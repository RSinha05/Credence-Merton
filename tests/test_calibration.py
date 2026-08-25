import pytest
import numpy as np
from model.calibration import DDCalibrator

def test_calibration_monotonicity():
    calibrator = DDCalibrator()
    
    # Fit with synthetic data
    dd_vals = np.linspace(1, 10, 100)
    # Give a smoother probability curve to ensure strict monotonicity
    defaults = np.exp(-dd_vals / 2)
    
    calibrator.fit(dd_vals, defaults)
    
    # Check predictions are monotonic
    test_dds = np.array([2.0, 4.0, 6.0])
    preds = calibrator.predict(test_dds)
    
    assert preds[0] > preds[1] > preds[2], "Predictions should strictly decrease as DD increases"

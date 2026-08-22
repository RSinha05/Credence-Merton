import logging
import numpy as np
import pandas as pd
from arch import arch_model
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

def fit_garch(
    log_returns: pd.Series,
    p: int = 1,
    q: int = 1,
    dist: str = 'normal',
    rescale: bool = True
) -> dict:
    r"""Fits a GARCH(p,q) model to log returns.
    
    The GARCH(1,1) conditional variance formula is:
    \sigma^2_t = \omega + \alpha \cdot \epsilon^2_{t-1} + \beta \cdot \sigma^2_{t-1}
    
    Args:
        log_returns (pd.Series): Time series of log returns.
        p (int): Lag order of the symmetric innovation.
        q (int): Lag order of lagged volatility.
        dist (str): Error distribution ('normal', 't', 'skewt', etc.).
        rescale (bool): Whether to scale returns by 100 for numerical stability.
        
    Returns:
        dict: Dictionary containing fitted parameters and model details.
    """
    try:
        # Scale returns if requested
        if rescale:
            data = log_returns * 100
        else:
            data = log_returns
            
        # Initialize and fit model
        am = arch_model(data, vol='Garch', p=p, q=q, dist=dist)
        res = am.fit(disp='off')
        
        # Extract parameters
        omega = res.params.get('omega', 0.0)
        alpha = res.params.get('alpha[1]', 0.0)
        beta = res.params.get('beta[1]', 0.0)
        persistence = alpha + beta
        
        # Get conditional volatility
        cond_vol = res.conditional_volatility
        if rescale:
            cond_vol = cond_vol / 100
            omega = omega / (100**2)
            
        logger.info(f"GARCH({p},{q}) fitted. Omega: {omega:.6f}, Alpha: {alpha:.4f}, Beta: {beta:.4f}, Persistence: {persistence:.4f}")
        
        return {
            'omega': omega,
            'alpha': alpha,
            'beta': beta,
            'persistence': persistence,
            'log_likelihood': res.loglikelihood,
            'aic': res.aic,
            'bic': res.bic,
            'conditional_volatility': cond_vol,
            'model': res
        }
    except Exception as e:
        logger.error(f"Failed to fit GARCH model: {e}")
        raise

def forecast_volatility(
    log_returns: pd.Series,
    horizon: int = 1,
    annualize: bool = True,
    p: int = 1,
    q: int = 1
) -> dict:
    r"""Fits GARCH and produces a forward-looking volatility forecast.
    
    Args:
        log_returns (pd.Series): Time series of log returns.
        horizon (int): Forecast horizon in steps (days).
        annualize (bool): Whether to annualize the output volatilities.
        p (int): Lag order of the symmetric innovation.
        q (int): Lag order of lagged volatility.
        
    Returns:
        dict: Volatility forecasts and comparisons.
    """
    fit_res = fit_garch(log_returns, p=p, q=q)
    model_res = fit_res['model']
    
    # Forecast
    forecasts = model_res.forecast(horizon=horizon, reindex=False)
    # Get variance forecast for the final step, then square root for vol
    variance_forecast = forecasts.variance.iloc[-1].iloc[-1]
    
    if fit_res.get('persistence', 1.0) >= 1.0 or pd.isna(variance_forecast):
        logger.warning("Invalid variance forecast or non-stationary model.")
        raise ValueError("Invalid GARCH forecast.")
        
    garch_vol = np.sqrt(variance_forecast)
    if 'omega' in fit_res:
         # Rescale the forecasted volatility back if the model fitted data * 100
         garch_vol = garch_vol / 100
    
    hist_vol = log_returns.std()
    
    if annualize:
        garch_vol_ann = garch_vol * np.sqrt(252)
        hist_vol_ann = hist_vol * np.sqrt(252)
        cond_vol_ann = fit_res['conditional_volatility'] * np.sqrt(252)
    else:
        garch_vol_ann = garch_vol
        hist_vol_ann = hist_vol
        cond_vol_ann = fit_res['conditional_volatility']
        
    vol_ratio = garch_vol_ann / hist_vol_ann if hist_vol_ann > 0 else 1.0
    
    logger.info(f"GARCH vol: {garch_vol_ann*100:.2f}% vs Historical: {hist_vol_ann*100:.2f}% (ratio: {vol_ratio:.2f})")
    
    return {
        'garch_vol_annualized': float(garch_vol_ann),
        'historical_vol_annualized': float(hist_vol_ann),
        'vol_ratio': float(vol_ratio),
        'conditional_vol_series': cond_vol_ann,
        'garch_params': {
            'omega': fit_res['omega'],
            'alpha': fit_res['alpha'],
            'beta': fit_res['beta'],
            'persistence': fit_res['persistence']
        }
    }

def compute_garch_enhanced_equity_vol(
    log_returns: pd.Series,
    fallback_to_historical: bool = True
) -> Tuple[float, str]:
    r"""Computes equity volatility using GARCH with a fallback to historical standard deviation.
    
    This replaces naive trailing historical standard deviation of equity returns 
    with a GARCH(1,1) forward-looking volatility forecast.
    
    Args:
        log_returns (pd.Series): Daily log returns.
        fallback_to_historical (bool): Fall back to std() if GARCH fails.
        
    Returns:
        Tuple[float, str]: (annualized_volatility, method_used)
    """
    try:
        if len(log_returns) < 50:
            raise ValueError("Not enough data to fit GARCH.")
            
        res = forecast_volatility(log_returns, horizon=1, annualize=True)
        
        # Check stability
        if res['garch_params']['persistence'] >= 1.0:
            logger.warning("GARCH persistence >= 1.0. Model is non-stationary.")
            raise ValueError("Non-stationary GARCH model.")
            
        return res['garch_vol_annualized'], 'garch'
        
    except Exception as e:
        logger.warning(f"GARCH volatility estimation failed: {e}. Falling back to historical.")
        if fallback_to_historical:
            hist_vol = log_returns.std() * np.sqrt(252)
            return hist_vol, 'historical'
        else:
            raise

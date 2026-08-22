import os
import logging
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

def fetch_risk_free_rate(maturity: str = '1Y', default_fallback: float = 0.045) -> float:
    """
    Fetch the risk-free rate using a 4-tier cascading fallback.
    
    Tiers:
        1. fredapi (if FRED_API_KEY is set)
        2. FRED public CSV
        3. Yahoo Finance (^IRX)
        4. Static default

    Args:
        maturity (str): Maturity to fetch ('1Y' or '3M').
        default_fallback (float): The default rate if all else fails.

    Returns:
        float: Risk-free rate as a decimal (e.g., 0.0435).
    """
    series_id = 'DGS3MO' if maturity.upper() == '3M' else 'DGS1'
    
    # Tier 1: fredapi
    try:
        api_key = os.environ.get('FRED_API_KEY')
        if api_key:
            from fredapi import Fred
            fred = Fred(api_key=api_key)
            series = fred.get_series(series_id)
            val = series.dropna().iloc[-1]
            logger.info("Successfully fetched risk-free rate using fredapi (Tier 1).")
            return float(val / 100.0)
    except Exception as e:
        logger.warning(f"Tier 1 (fredapi) failed: {e}")
        
    # Tier 2: FRED public CSV
    try:
        csv_url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        df = pd.read_csv(csv_url, parse_dates=['DATE'], na_values='.')
        val = df[series_id].dropna().iloc[-1]
        logger.info("Successfully fetched risk-free rate using FRED public CSV (Tier 2).")
        return float(val / 100.0)
    except Exception as e:
        logger.warning(f"Tier 2 (FRED CSV) failed: {e}")
        
    # Tier 3: Yahoo Finance
    try:
        # For 3M rate we can use ^IRX (13-week Treasury Bill).
        # For 1Y rate, yfinance doesn't have a reliable direct ticker always available, but we'll try ^IRX.
        tkr = yf.Ticker('^IRX')
        hist = tkr.history(period='1mo')
        if not hist.empty:
            val = hist['Close'].dropna().iloc[-1]
            logger.info("Successfully fetched risk-free rate using Yahoo Finance (Tier 3).")
            return float(val / 100.0)
    except Exception as e:
        logger.warning(f"Tier 3 (Yahoo Finance) failed: {e}")
        
    # Tier 4: Static default
    logger.warning(f"All tiers failed. Using static default risk-free rate: {default_fallback} (Tier 4).")
    return default_fallback

import logging
import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

def fetch_equity_data(ticker: str, lookback_days: int = 252) -> pd.DataFrame:
    """
    Fetch equity data and compute market cap and log returns.

    Args:
        ticker (str): The stock ticker symbol.
        lookback_days (int): The number of days of history to return. Defaults to 252.

    Returns:
        pd.DataFrame: DataFrame containing 'date', 'close', 'mkt_cap', 'log_return'.
    """
    try:
        tkr = yf.Ticker(ticker)
        hist = tkr.history(period='2y')
        
        if hist.empty:
            logger.error(f"No history found for ticker {ticker}.")
            raise ValueError(f"No history found for ticker {ticker}.")
        
        try:
            shares_outstanding = tkr.info['sharesOutstanding']
        except KeyError:
            logger.error(f"Shares outstanding not found in info for {ticker}.")
            raise ValueError(f"Shares outstanding not found for {ticker}.")
        
        df = hist[['Close']].copy()
        df.reset_index(inplace=True)
        df.rename(columns={'Date': 'date', 'Close': 'close'}, inplace=True)
        
        df['mkt_cap'] = df['close'] * shares_outstanding
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))
        
        # Return the last lookback_days rows
        return df.tail(lookback_days)
    except Exception as e:
        logger.error(f"Error fetching equity data for {ticker}: {e}")
        raise

def compute_equity_volatility(log_returns: pd.Series) -> float:
    r"""
    Compute annualized equity volatility from log returns.
    
    Formula:
        \sigma_E = \text{std}(\text{log\_returns}) \times \sqrt{252}
    
    Args:
        log_returns (pd.Series): Series of log returns.

    Returns:
        float: Annualized equity volatility.
    """
    valid_returns = log_returns.dropna()
    if valid_returns.empty:
        logger.error("Log returns series is empty after dropping NaNs.")
        raise ValueError("Log returns series is empty.")
    
    return float(np.std(valid_returns, ddof=1) * np.sqrt(252))

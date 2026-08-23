import logging
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from workers.celery_app import celery_app
from data.equity import fetch_equity_data
from data.edgar import SECEdgarClient
from data.risk_free import fetch_risk_free_rate
from model.ensemble import run_full_assessment

logger = logging.getLogger(__name__)

def _serialize_pandas(obj):
    if isinstance(obj, pd.Series):
        return {str(k): v for k, v in obj.to_dict().items()}
    elif isinstance(obj, pd.DataFrame):
        return {str(k): _serialize_pandas(v) for k, v in obj.to_dict(orient='index').items()}
    elif isinstance(obj, dict):
        return {k: _serialize_pandas(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_pandas(i) for i in obj]
    return obj

@celery_app.task(bind=True, name='risk.analyze_single_firm')
def analyze_single_firm_task(self, ticker: str, time_horizon: float = 1.0) -> dict:
    logger.info(f"Starting single firm analysis for {ticker}")
    self.update_state(state='PROGRESS', meta={'status': 'Initializing data fetch'})
    
    try:
        rf_rate = fetch_risk_free_rate()
        equity_data = fetch_equity_data(ticker)
        
        edgar_client = SECEdgarClient()
        debt_data = edgar_client.extract_debt_data(ticker)
        
        market_cap = equity_data.iloc[-1]['mkt_cap']
        
        result = run_full_assessment(
            ticker=ticker,
            equity_series=equity_data['mkt_cap'],
            D=debt_data['default_point'],
            r=rf_rate,
            market_cap=market_cap,
            T=time_horizon
        )
        
        serializable_result = _serialize_pandas(result)
        logger.info(f"Successfully completed analysis for {ticker}")
        return serializable_result
        
    except Exception as e:
        logger.error(f"Error during analysis of {ticker}: {str(e)}", exc_info=True)
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(bind=True, name='risk.analyze_portfolio')
def analyze_portfolio_task(self, tickers: list, time_horizon: float = 1.0) -> dict:
    logger.info(f"Starting portfolio analysis for {len(tickers)} tickers")
    results = {}
    errors = {}
    
    total = len(tickers)
    for idx, ticker in enumerate(tickers):
        self.update_state(state='PROGRESS', meta={'current': idx, 'total': total, 'status': f'Analyzing {ticker}'})
        try:
            rf_rate = fetch_risk_free_rate()
            equity_data = fetch_equity_data(ticker)
            edgar_client = SECEdgarClient()
            debt_data = edgar_client.extract_debt_data(ticker)
            market_cap = equity_data.iloc[-1]['mkt_cap']
            
            res = run_full_assessment(
                ticker=ticker,
                equity_series=equity_data['mkt_cap'],
                D=debt_data['default_point'],
                r=rf_rate,
                market_cap=market_cap,
                T=time_horizon
            )
            results[ticker] = _serialize_pandas(res)
        except Exception as e:
            logger.error(f"Error analyzing {ticker} in portfolio task: {str(e)}")
            errors[ticker] = str(e)
            
    self.update_state(state='PROGRESS', meta={'current': total, 'total': total, 'status': 'Completed'})
    logger.info("Portfolio analysis finished")
    return {"results": results, "errors": errors}

@celery_app.task(name='risk.refresh_risk_free_rate')
def refresh_risk_free_rate_task() -> float:
    logger.info("Starting refresh of risk free rate")
    try:
        rate = fetch_risk_free_rate()
        logger.info(f"Risk free rate refreshed successfully: {rate}")
        return float(rate)
    except Exception as e:
        logger.error(f"Failed to refresh risk free rate: {str(e)}")
        raise

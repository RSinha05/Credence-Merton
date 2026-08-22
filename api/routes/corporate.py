import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks

from api.schemas import (
    CorporateRiskRequest, CorporateRiskResponse, PortfolioRiskRequest, PortfolioRiskResponse
)

try:
    from data.equity import fetch_equity_data, compute_equity_volatility
    from data.edgar import SECEdgarClient
    from data.risk_free import fetch_risk_free_rate
    from model.merton import run_single_firm
    from model.altman_z import run_altman_z
    from model.ensemble import compute_ensemble_risk
except ImportError:
    # Dummy fallbacks for imports if they are not yet implemented
    pass

router = APIRouter(prefix='/api/v1/risk', tags=['Corporate Risk'])
logger = logging.getLogger(__name__)

_RISK_FREE_RATE_CACHE = None

def get_cached_risk_free_rate() -> float:
    """Get the cached risk-free rate, fetching it if not already cached."""
    global _RISK_FREE_RATE_CACHE
    if _RISK_FREE_RATE_CACHE is None:
        try:
            _RISK_FREE_RATE_CACHE = fetch_risk_free_rate()
            logger.info(f"Fetched new risk-free rate: {_RISK_FREE_RATE_CACHE}")
        except Exception as e:
            logger.warning(f"Could not fetch risk-free rate: {e}. Defaulting to 0.04.")
            _RISK_FREE_RATE_CACHE = 0.04
    return _RISK_FREE_RATE_CACHE

@router.post('/corporate/{ticker}', response_model=CorporateRiskResponse)
async def analyze_corporate_risk(ticker: str, request: Optional[CorporateRiskRequest] = None):
    """
    Analyze corporate risk for a given ticker using the Merton and optionally Altman Z models.
    """
    if request is None:
        request = CorporateRiskRequest(ticker=ticker)
        
    logger.info(f"Analyzing corporate risk for {ticker}")
    
    try:
        rf_rate = get_cached_risk_free_rate()
        
        # 1. Fetch equity data
        try:
            equity_data = fetch_equity_data(ticker)
            equity_vol = compute_equity_volatility(equity_data)
        except Exception as e:
            logger.error(f"Ticker not found or equity data error for {ticker}: {e}")
            raise HTTPException(status_code=404, detail=f"Data for ticker {ticker} not found.")

        # 2. Fetch EDGAR debt data
        edgar_client = SECEdgarClient()
        debt_data = edgar_client.get_debt_data(ticker) # Assuming method name
        
        # 3. Run Merton model
        merton_res = run_single_firm(equity_data, debt_data, rf_rate, request.time_horizon)
        
        # 4. Run Altman Z (Optional)
        altman_res = None
        if request.include_altman:
            altman_res = run_altman_z(ticker)
            
        # 5. Compute Ensemble
        ensemble_res = None
        if altman_res:
            ensemble_res = compute_ensemble_risk(merton_res, altman_res)
            
        return CorporateRiskResponse(
            ticker=ticker,
            name=f"{ticker} Corporation", # Placeholder since we don't have a name fetcher in this snippet
            sp_rating="Implied", # Placeholder
            computed_at=datetime.utcnow(),
            merton=merton_res,
            altman=altman_res,
            ensemble=ensemble_res,
            dd_timeseries=None,
            pd_term_structure=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Internal computation error for {ticker}")
        raise HTTPException(status_code=500, detail="Internal computation error during risk analysis.")

@router.get('/corporate/{ticker}/history')
async def get_risk_history(ticker: str, days: int = 30):
    """
    Get historical risk metrics. DB integration coming in Phase 2.
    """
    logger.info(f"Fetching history for {ticker} over {days} days")
    return {"message": "DB integration coming in Phase 2"}

@router.post('/portfolio', response_model=PortfolioRiskResponse)
async def analyze_portfolio(request: PortfolioRiskRequest):
    """
    Analyze risk for a portfolio of tickers.
    """
    logger.info(f"Analyzing portfolio for {len(request.tickers)} tickers")
    firms = []
    
    for ticker in request.tickers:
        try:
            corp_req = CorporateRiskRequest(
                ticker=ticker, 
                time_horizon=request.time_horizon
            )
            res = await analyze_corporate_risk(ticker, corp_req)
            firms.append(res)
        except HTTPException as e:
            logger.warning(f"Failed to process {ticker} for portfolio: {e.detail}")
        except Exception as e:
            logger.error(f"Unexpected error for {ticker} in portfolio: {e}")
            
    # Dummy aggregation for stats
    return PortfolioRiskResponse(
        firms=firms,
        portfolio_stats={
            "avg_pd": 0.0,
            "median_dd": 0.0,
            "worst_ticker": firms[0].ticker if firms else "N/A",
            "spearman_rho": 0.0
        }
    )

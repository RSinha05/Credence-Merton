import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks

from api.schemas import (
    CorporateRiskRequest, CorporateRiskResponse, PortfolioRiskRequest, PortfolioRiskResponse
)

try:
    from data.equity import fetch_equity_data
    from data.edgar import SECEdgarClient
    from data.risk_free import fetch_risk_free_rate
    from model.merton import run_single_firm
    from model.altman_z import run_altman_z
    from model.ensemble import run_full_assessment
except ImportError:
    pass

router = APIRouter(prefix='/api/v1/risk', tags=['Corporate Risk'])
logger = logging.getLogger(__name__)

_RISK_FREE_RATE_CACHE = None

def get_cached_risk_free_rate() -> float:
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
    if request is None:
        request = CorporateRiskRequest(ticker=ticker)
        
    logger.info(f"Analyzing corporate risk for {ticker}")
    
    try:
        rf_rate = get_cached_risk_free_rate()
        
        # 1. Fetch equity data
        try:
            equity_data = fetch_equity_data(ticker)
        except Exception as e:
            logger.error(f"Ticker not found or equity data error for {ticker}: {e}")
            raise HTTPException(status_code=404, detail=f"Data for ticker {ticker} not found.")

        # 2. Fetch EDGAR debt data
        edgar_client = SECEdgarClient()
        try:
            debt_data = edgar_client.extract_debt_data(ticker)
        except Exception as e:
            logger.error(f"EDGAR data error for {ticker}: {e}")
            raise HTTPException(status_code=400, detail=f"EDGAR debt data not found for {ticker}.")
            
        market_cap = equity_data.iloc[-1]['mkt_cap']
        
        if request.include_altman:
            # Run full assessment (ensemble)
            res = run_full_assessment(
                ticker=ticker,
                equity_series=equity_data['mkt_cap'],
                D=debt_data.get('default_point_series', debt_data['default_point']),
                r=rf_rate,
                market_cap=market_cap,
                T=request.time_horizon
            )
            merton_res = res['merton']
            altman_res = res['altman']
            ensemble_res = res['ensemble']
        else:
            # Run Merton only
            merton_res = run_single_firm(
                equity_series=equity_data['mkt_cap'],
                D=debt_data.get('default_point_series', debt_data['default_point']),
                r=rf_rate,
                T=request.time_horizon
            )
            altman_res = None
            ensemble_res = None
            
        # Serialize for DB insertion
        import numpy as np
        import pandas as pd
        def serialize_for_db(obj):
            if isinstance(obj, pd.Series):
                return {str(k): v for k, v in obj.to_dict().items()}
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, dict):
                return {k: serialize_for_db(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [serialize_for_db(i) for i in obj]
            return obj
        
        full_res = {'merton': merton_res, 'altman': altman_res, 'ensemble': ensemble_res}
        clean_res = serialize_for_db(full_res)
        
        firm = db.query(Firm).filter(Firm.ticker == ticker).first()
        if not firm:
            firm = Firm(ticker=ticker, name=f"{ticker} Corp", sp_rating="NR", moodys_rating="NR", sector="Unknown")
            db.add(firm)
            db.commit()
            db.refresh(firm)
            
        risk_record = RiskResult(firm_id=firm.id, model_type='corporate_ews', raw_output=clean_res)
        db.add(risk_record)
        db.commit()

        return CorporateRiskResponse(
            ticker=ticker,
            name=f"{ticker} Corporation",
            sp_rating="Implied",
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
    logger.info(f"Fetching history for {ticker} over {days} days")
    return {"message": "DB integration coming in Phase 2"}

@router.post('/portfolio', response_model=PortfolioRiskResponse)
async def analyze_portfolio(request: PortfolioRiskRequest):
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
            
    return PortfolioRiskResponse(
        firms=firms,
        portfolio_stats={
            "avg_pd": 0.0,
            "median_dd": 0.0,
            "worst_ticker": firms[0].ticker if firms else "N/A",
            "spearman_rho": 0.0
        }
    )

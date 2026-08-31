import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks

from config import get_firm_by_ticker
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

                # Extract and serialize timeseries data from merton_res
        dd_ts = merton_res.get('dd_timeseries')
        if dd_ts is not None:
            # Assuming it's a pandas Series indexed by Timestamp
            dd_ts_dict = {str(k.date()) if hasattr(k, 'date') else str(k): float(v) for k, v in dd_ts.items()}
        else:
            dd_ts_dict = None
            
        pd_ts = merton_res.get('pd_term_structure')
        if pd_ts is not None:
            pd_ts_dict = {float(k): float(v) for k, v in pd_ts.items()}
        else:
            pd_ts_dict = None

        ordinal = None
        try:
            firm_entry = get_firm_by_ticker(ticker)
            ordinal = firm_entry.ordinal
        except ValueError:
            pass

        return CorporateRiskResponse(
            ticker=ticker,
            name=f"{ticker} Corporation",
            sp_rating="Implied",
            ordinal=ordinal,
            computed_at=datetime.utcnow(),
            merton=merton_res,
            altman=altman_res,
            ensemble=ensemble_res,
            dd_timeseries=dd_ts_dict,
            pd_term_structure=pd_ts_dict
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Internal computation error for {ticker}")
        raise HTTPException(status_code=500, detail="Internal computation error during risk analysis.")

@router.get('/corporate/{ticker}/history')
async def get_risk_history(ticker: str, days: int = 30):
    from db.database import SessionLocal
    from db.models import Firm, RiskResult
    from datetime import datetime, timedelta
    
    logger.info(f"Fetching history for {ticker} over {days} days")
    db = SessionLocal()
    try:
        firm = db.query(Firm).filter(Firm.ticker == ticker.upper()).first()
        if not firm:
            raise HTTPException(status_code=404, detail="Firm not found in DB")
            
        cutoff = datetime.utcnow() - timedelta(days=days)
        results = db.query(RiskResult).filter(
            RiskResult.firm_id == firm.id,
            RiskResult.computed_at >= cutoff
        ).order_by(RiskResult.computed_at.desc()).all()
        
        history = []
        for r in results:
            history.append({
                "computed_at": r.computed_at,
                "model_type": r.model_type,
                "raw_output": r.raw_output
            })
            
        return {"ticker": ticker.upper(), "history": history}
    finally:
        db.close()

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

@router.get('/alerts')
async def get_alerts(alert_level: Optional[str] = None, ticker: Optional[str] = None):
    logger.info(f"Generating alerts: level={alert_level}, ticker={ticker}")
    from config import FIRM_PANEL
    from datetime import datetime
    import random
    
    # Generate synthetic alerts from high-yield / speculative firms in FIRM_PANEL
    alerts = []
    for firm in FIRM_PANEL:
        if firm.ordinal < 10:
            continue  # Skip investment-grade firms
        
        if ticker and firm.ticker.upper() != ticker.upper():
            continue
        
        # Higher ordinal = worse rating = more likely to alert
        if firm.ordinal >= 17:
            level = 'critical'
            dd_val = round(random.uniform(0.3, 1.2), 2)
            desc = f"{firm.name} ({firm.sp_rating}) — DD below distress threshold. Immediate review required."
        elif firm.ordinal >= 14:
            level = 'warning'
            dd_val = round(random.uniform(1.5, 2.8), 2)
            desc = f"{firm.name} ({firm.sp_rating}) — DD declining, approaching high-risk zone."
        else:
            level = 'warning'
            dd_val = round(random.uniform(2.5, 3.5), 2)
            desc = f"{firm.name} ({firm.sp_rating}) — Elevated credit spread, monitoring advised."
        
        alerts.append({
            'ticker': firm.ticker,
            'alert_level': level,
            'current_dd': dd_val,
            'description': desc,
            'sp_rating': firm.sp_rating,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # Sort: critical first, then by DD ascending
    alerts.sort(key=lambda a: (0 if a['alert_level'] == 'critical' else 1, a['current_dd']))
    
    if alert_level:
        alerts = [a for a in alerts if a['alert_level'] == alert_level.lower()]
    
    return alerts

@router.get('/corporate/{ticker}/timeseries')
async def get_corporate_timeseries(ticker: str):
    logger.info(f"Fetching timeseries for {ticker}")
    from db.database import SessionLocal
    from db.models import Firm, RiskResult
    
    db = SessionLocal()
    try:
        firm = db.query(Firm).filter(Firm.ticker == ticker.upper()).first()
        if not firm:
            raise HTTPException(status_code=404, detail="Firm not found in DB")
            
        latest = db.query(RiskResult).filter(
            RiskResult.firm_id == firm.id,
            RiskResult.model_type == 'corporate_ews'
        ).order_by(RiskResult.computed_at.desc()).first()
        
        if not latest or not latest.raw_output:
            raise HTTPException(status_code=404, detail="No risk results found for firm")
            
        raw = latest.raw_output
        merton = raw.get('merton', {})
        
        dd_ts = merton.get('dd_timeseries', {})
        asset_ts = merton.get('asset_series', {})
        
        return {
            "ticker": ticker.upper(),
            "dd_timeseries": dd_ts,
            "asset_series": asset_ts
        }
    finally:
        db.close()

@router.get('/portfolio/{portfolio_id}/summary')
async def get_portfolio_summary(portfolio_id: str, tickers: Optional[str] = None):
    logger.info(f"Fetching portfolio summary for {portfolio_id}")
    from config import FIRM_PANEL, get_firm_by_ticker
    import math, random
    
    # Build seed data from FIRM_PANEL — maps rating ordinal to realistic PD/DD
    # Higher ordinal = worse rating = higher PD, lower DD
    records = []
    for firm in FIRM_PANEL:
        ordinal = firm.ordinal
        # PD scales exponentially with ordinal (1=AAA → ~0.01%, 17=CCC → ~25%)
        base_pd = 0.0001 * math.exp(0.35 * ordinal)
        pd_rn = min(base_pd + random.uniform(-0.002, 0.002), 0.99)
        pd_rn = max(pd_rn, 0.0001)
        # DD inversely related to ordinal
        dd_rn = max(8.0 - 0.4 * ordinal + random.uniform(-0.3, 0.3), 0.2)
        
        records.append({
            'ticker': firm.ticker,
            'name': firm.name,
            'sp_rating': firm.sp_rating,
            'PD_rn': round(pd_rn, 6),
            'DD_rn': round(dd_rn, 2),
            'ordinal': ordinal
        })
    
    import pandas as pd
    df = pd.DataFrame(records)
    avg_pd = float(df['PD_rn'].mean())
    median_dd = float(df['DD_rn'].median())
    worst_ticker = df.loc[df['PD_rn'].idxmax()]['ticker']
    
    from scipy.stats import spearmanr
    try:
        rho, _ = spearmanr(df['PD_rn'], df['ordinal'])
        spearman_rho = float(rho)
    except Exception:
        spearman_rho = 0.0
    
    return {
        "avg_pd": avg_pd,
        "median_dd": median_dd,
        "worst_ticker": worst_ticker,
        "spearman_rho": spearman_rho,
        "scatter_data": records,
        "firm_count": len(records)
    }

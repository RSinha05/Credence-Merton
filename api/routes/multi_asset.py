import yaml
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from model.merton import run_single_firm
from data.equity import fetch_equity_data
from data.fundamentals import UniversalFundamentals
from data.risk_free import fetch_risk_free_rate

from model.etf_risk import ETFRiskEngine
from model.fixed_income import FixedIncomeEngine

from db.database import get_db
from db.models import Firm, RiskResult

router = APIRouter(prefix='/api/v1/risk/multi-asset', tags=['Multi-Asset Risk'])
logger = logging.getLogger(__name__)

def load_universe() -> dict:
    try:
        with open('universe.yaml', 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}

def determine_asset_class(ticker: str, universe: dict) -> str:
    for category, tickers in universe.items():
        if ticker in tickers:
            if 'equities' in category:
                return 'EQUITY'
            elif 'etfs' in category:
                return 'ETF'
            elif 'bonds' in category:
                return 'BOND'
    if '^' in ticker: return 'BOND'
    return 'EQUITY'

@router.get('/{ticker}')
async def analyze_multi_asset(ticker: str, db: Session = Depends(get_db)):
    logger.info(f"Analyzing multi-asset risk for {ticker}")
    universe = load_universe()
    asset_class = determine_asset_class(ticker, universe)
    
    try:
        # Check if firm/asset exists in DB, if not create it
        firm = db.query(Firm).filter(Firm.ticker == ticker).first()
        if not firm:
            firm = Firm(ticker=ticker, name=ticker, sector=asset_class)
            db.add(firm)
            db.commit()
            db.refresh(firm)
            
        if asset_class == 'EQUITY':
            rf_rate = fetch_risk_free_rate()
            equity_data = fetch_equity_data(ticker)
            market_cap = equity_data.iloc[-1]['mkt_cap']
            
            fund = UniversalFundamentals(ticker)
            debt_data = fund.extract_debt_data()
            
            res = run_single_firm(
                equity_series=equity_data['mkt_cap'],
                D=debt_data['default_point'],
                r=rf_rate,
                T=1.0
            )
            
            # Persist to Supabase / DB
            risk_record = RiskResult(
                firm_id=firm.id,
                model_type='merton',
                time_horizon=1.0,
                risk_free_rate=rf_rate,
                sigma_v=res.get('sigma_V'),
                dd_risk_neutral=res.get('DD_rn'),
                pd_risk_neutral=res.get('PD_rn'),
                asset_value=res.get('V_current'),
                default_point=debt_data['default_point'],
                raw_output={"asset_class": "EQUITY", **res}
            )
            db.add(risk_record)
            db.commit()
            
            return {"asset_type": "EQUITY", "ticker": ticker, "metrics": res}
            
        elif asset_class == 'ETF':
            engine = ETFRiskEngine(ticker)
            res = engine.run_assessment()
            
            risk_record = RiskResult(
                firm_id=firm.id,
                model_type='etf_risk',
                raw_output=res
            )
            db.add(risk_record)
            db.commit()
            
            return {"ticker": ticker, **res}
            
        elif asset_class == 'BOND':
            engine = FixedIncomeEngine(ticker)
            res = engine.run_assessment()
            
            risk_record = RiskResult(
                firm_id=firm.id,
                model_type='fixed_income',
                raw_output=res
            )
            db.add(risk_record)
            db.commit()
            
            return {"ticker": ticker, **res}
            
        else:
            raise HTTPException(status_code=400, detail="Unknown asset class")
            
    except Exception as e:
        logger.exception(f"Error analyzing {ticker}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/{ticker}/history')
async def get_history(ticker: str, limit: int = 10, db: Session = Depends(get_db)):
    """Fetch historical runs from Supabase."""
    firm = db.query(Firm).filter(Firm.ticker == ticker).first()
    if not firm:
        raise HTTPException(status_code=404, detail="Ticker not found in database")
        
    results = db.query(RiskResult).filter(RiskResult.firm_id == firm.id).order_by(RiskResult.computed_at.desc()).limit(limit).all()
    return {"ticker": ticker, "history": [r.raw_output for r in results if r.raw_output]}

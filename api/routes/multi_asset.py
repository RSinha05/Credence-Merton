import yaml
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import numpy as np

from model.merton import run_single_firm
from data.equity import fetch_equity_data
from data.fundamentals import UniversalFundamentals
from data.risk_free import fetch_risk_free_rate

from model.etf_risk import ETFRiskEngine
from model.fixed_income import FixedIncomeEngine
from api.routes.nlp import get_nlp_sentiment

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
            if 'equities' in category: return 'EQUITY'
            elif 'etfs' in category: return 'ETF'
            elif 'bonds' in category: return 'BOND'
    if '^' in ticker: return 'BOND'
    if ticker in ['SPY', 'QQQ', 'DIA', 'IWM', 'VOO', 'HYG', 'LQD', 'TLT', 'NIFTYBEES.NS', 'BANKBEES.NS', 'LIQUIDBEES.NS']: return 'ETF'
    return 'EQUITY'

@router.get('/{ticker}')
async def analyze_multi_asset(ticker: str, db: Session = Depends(get_db)):
    logger.info(f"Analyzing multi-asset risk for {ticker}")
    universe = load_universe()
    asset_class = determine_asset_class(ticker, universe)
    
    try:
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
            
            sentiment_score = 0.0
            try:
                nlp_res = get_nlp_sentiment(ticker, db)
                sentiment_score = nlp_res.get("sentiment_score", 0.0)
            except Exception as e:
                logger.warning(f"Failed NLP: {e}")
            
            res = run_single_firm(
                equity_series=equity_data['mkt_cap'],
                D=debt_data.get('default_point_series', debt_data['default_point']),
                r=rf_rate,
                T=1.0,
                sentiment_score=sentiment_score
            )
            res["sentiment_score"] = float(sentiment_score)
            
            # Serialize for response
            if 'asset_series' in res and hasattr(res['asset_series'], 'to_dict'):
                res['asset_series'] = {str(k): float(v) for k, v in res['asset_series'].to_dict().items()}
            if 'dd_timeseries' in res and hasattr(res['dd_timeseries'], 'to_dict'):
                res['dd_timeseries'] = {str(k): float(v) for k, v in res['dd_timeseries'].to_dict().items()}
                
            # Cast numpy types for DB
            clean_res = {}
            for k, v in res.items():
                if isinstance(v, (np.float64, np.float32)): clean_res[k] = float(v)
                elif isinstance(v, (np.int64, np.int32)): clean_res[k] = int(v)
                elif isinstance(v, (float, int, str, bool, type(None))): clean_res[k] = v
            clean_res['asset_class'] = 'EQUITY'
            
            # Cast direct DB assignments to standard Python types
            sigma_v = float(res.get('sigma_V')) if res.get('sigma_V') is not None else None
            dd_rn = float(res.get('DD_rn')) if res.get('DD_rn') is not None else None
            pd_rn = float(res.get('PD_rn')) if res.get('PD_rn') is not None else None
            v_curr = float(res.get('V_current')) if res.get('V_current') is not None else None
            d_point = float(debt_data['default_point']) if debt_data.get('default_point') is not None else None
            
            risk_record = RiskResult(
                firm_id=firm.id,
                model_type='merton',
                time_horizon=1.0,
                risk_free_rate=float(rf_rate) if rf_rate is not None else None,
                sigma_v=sigma_v,
                dd_risk_neutral=dd_rn,
                pd_risk_neutral=pd_rn,
                asset_value=v_curr,
                default_point=float(debt_data['default_point']) if debt_data.get('default_point') is not None else None,
                raw_output=clean_res
            )
            db.add(risk_record)
            db.commit()
            
            return {"asset_type": "EQUITY", "ticker": ticker, "metrics": res}
            
        elif asset_class == 'ETF':
            engine = ETFRiskEngine(ticker)
            res = engine.run_assessment()
            risk_record = RiskResult(firm_id=firm.id, model_type='etf_risk', raw_output=res)
            db.add(risk_record)
            db.commit()
            return {"ticker": ticker, **res}
            
        elif asset_class == 'BOND':
            engine = FixedIncomeEngine(ticker)
            res = engine.run_assessment()
            risk_record = RiskResult(firm_id=firm.id, model_type='fixed_income', raw_output=res)
            db.add(risk_record)
            db.commit()
            return {"ticker": ticker, **res}
            
        else:
            raise HTTPException(status_code=400, detail="Unknown asset class")
            
    except Exception as e:
        logger.exception(f"Error analyzing {ticker}")
        raise HTTPException(status_code=500, detail=str(e))

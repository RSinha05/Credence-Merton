import yaml
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from model.merton import run_single_firm
from model.ensemble import run_full_assessment
from data.equity import fetch_equity_data
from data.fundamentals import UniversalFundamentals
from data.risk_free import fetch_risk_free_rate

from model.etf_risk import ETFRiskEngine
from model.fixed_income import FixedIncomeEngine

router = APIRouter(prefix='/api/v1/risk/multi-asset', tags=['Multi-Asset Risk'])
logger = logging.getLogger(__name__)

# Load Universe mapping
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
    # Fallback heuristic
    if '^' in ticker: return 'BOND'
    return 'EQUITY' # Assume stock by default

@router.get('/{ticker}')
async def analyze_multi_asset(ticker: str):
    logger.info(f"Analyzing multi-asset risk for {ticker}")
    universe = load_universe()
    asset_class = determine_asset_class(ticker, universe)
    
    try:
        if asset_class == 'EQUITY':
            # Run Universal Corporate Risk
            rf_rate = fetch_risk_free_rate()
            equity_data = fetch_equity_data(ticker)
            market_cap = equity_data.iloc[-1]['mkt_cap']
            
            fund = UniversalFundamentals(ticker)
            debt_data = fund.extract_debt_data()
            
            # Since we replaced EDGAR with Universal, run_full_assessment needs tweaks or we just run Merton directly
            # For simplicity in this multi-asset route, we run Merton.
            res = run_single_firm(
                equity_series=equity_data['mkt_cap'],
                D=debt_data['default_point'],
                r=rf_rate,
                T=1.0
            )
            return {"asset_type": "EQUITY", "ticker": ticker, "metrics": res}
            
        elif asset_class == 'ETF':
            engine = ETFRiskEngine(ticker)
            return {"ticker": ticker, **engine.run_assessment()}
            
        elif asset_class == 'BOND':
            engine = FixedIncomeEngine(ticker)
            return {"ticker": ticker, **engine.run_assessment()}
            
        else:
            raise HTTPException(status_code=400, detail="Unknown asset class")
            
    except Exception as e:
        logger.exception(f"Error analyzing {ticker}")
        raise HTTPException(status_code=500, detail=str(e))

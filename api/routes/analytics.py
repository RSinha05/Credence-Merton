import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from data.equity import fetch_equity_data
from data.edgar import SECEdgarClient
from data.risk_free import fetch_risk_free_rate
from model.merton import run_single_firm
from model.ensemble import run_full_assessment
from model.regulatory_capital import compute_capital_requirement
from model.ttc_pit import compute_ttc_pit_comparison, dd_to_rating_bucket
from model.cecl import compute_cecl_expected_loss
from model.stress_testing import run_stress_test, STRESS_SCENARIOS
from model.portfolio_risk import vasicek_analytical_var
from model.migration import dd_to_rating

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

# Simple in-memory cache for risk-free rate
_rf_cache = None

def get_cached_rf() -> float:
    global _rf_cache
    if _rf_cache is None:
        try:
            _rf_cache = fetch_risk_free_rate()
        except Exception as e:
            # Fallback in case of fetching error
            _rf_cache = 0.04
    return _rf_cache

def serialize_for_db(obj: Any) -> Any:
    if isinstance(obj, (np.float32, np.float64, np.float16)):
        return float(obj)
    if isinstance(obj, (np.int32, np.int64, np.int16, np.int8)):
        return int(obj)
    if isinstance(obj, pd.Series):
        return {str(k): serialize_for_db(v) for k, v in obj.items()}
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    if isinstance(obj, dict):
        return {k: serialize_for_db(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_for_db(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [serialize_for_db(v) for v in obj.tolist()]
    return obj

@router.get("/deep/{ticker}")
async def get_deep_analytics(ticker: str) -> Dict[str, Any]:
    try:
        # Fetch data
        equity_df = fetch_equity_data(ticker)
        if equity_df is None or equity_df.empty:
            raise HTTPException(status_code=404, detail="Equity data not found")
        
        edgar = SECEdgarClient()
        try:
            debt_data = edgar.extract_debt_data(ticker)
            D = debt_data.get('default_point_series', debt_data.get('default_point', 1000.0))
        except Exception:
            D = 1000.0  # Fallback
            
        r = get_cached_rf()
        
        # Run Merton
        merton_results = run_single_firm(equity_df['mkt_cap'], D, r)
        
        # Basel IRB Regulatory Capital
        reg_cap = compute_capital_requirement(pd_val=merton_results["PD_rn"])
        
        # TTC/PIT Comparison
        ttc_pit = compute_ttc_pit_comparison(merton_results)
        
        # CECL Expected Loss
        cecl_res = compute_cecl_expected_loss(merton_results)
        
        # Implied Rating
        rating = dd_to_rating(merton_results["DD_rn"])
        
        # Assemble Response
        response = {
            "ticker": ticker,
            "merton": {
                "V_current": merton_results.get("V_current"),
                "sigma_V": merton_results.get("sigma_V"),
                "DD_rn": merton_results.get("DD_rn"),
                "PD_rn": merton_results.get("PD_rn"),
                "DD_rw": merton_results.get("DD_rw"),
                "PD_rw": merton_results.get("PD_rw"),
                "D": merton_results.get("D")
            },
            "regulatory_capital": reg_cap,
            "ttc_pit": ttc_pit,
            "cecl": cecl_res,
            "implied_rating": rating
        }
        
        return serialize_for_db(response)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stress/{ticker}")
async def get_stress_test(ticker: str) -> Dict[str, Any]:
    try:
        equity_df = fetch_equity_data(ticker)
        if equity_df is None or equity_df.empty:
            raise HTTPException(status_code=404, detail="Equity data not found")
            
        edgar = SECEdgarClient()
        try:
            debt_data = edgar.extract_debt_data(ticker)
            D = debt_data.get('default_point', 1000.0) # stress test expects float
        except Exception:
            D = 1000.0  # Fallback
            
        r = get_cached_rf()
        
        stress_res = run_stress_test(equity_df['mkt_cap'], D, r)
        
        return serialize_for_db(stress_res)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scenarios")
async def list_scenarios() -> Dict[str, Any]:
    return STRESS_SCENARIOS

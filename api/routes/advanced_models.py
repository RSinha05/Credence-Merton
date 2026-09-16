import logging
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

from model.counterparty import CounterpartyRiskEngine
from model.stress_testing import run_stress_test, STRESS_SCENARIOS

router = APIRouter(prefix='/api/v1/advanced', tags=['Advanced Models'])
logger = logging.getLogger(__name__)

# Models for Counterparty
class CvaRequest(BaseModel):
    initial_value: float = 1_000_000.0
    volatility: float = 0.20
    horizon_years: float = 5.0
    steps: int = 60
    lgd: float = 0.40
    risk_free_rate: float = 0.04
    pd_start: float = 0.01
    pd_end: float = 0.10

class CvaResponse(BaseModel):
    cva: float
    pfe_95: List[float]
    expected_exposure: List[float]
    time_grid: List[float]

@router.post('/cva', response_model=CvaResponse)
def calculate_cva(req: CvaRequest):
    try:
        engine = CounterpartyRiskEngine(n_simulations=5000)
        exposure = engine.simulate_exposure(
            initial_value=req.initial_value,
            volatility=req.volatility,
            horizon_years=req.horizon_years,
            steps=req.steps
        )
        cum_pd = np.linspace(req.pd_start, req.pd_end, req.steps)
        res = engine.calculate_cva(
            exposure_paths=exposure,
            pd_term_structure=cum_pd,
            lgd=req.lgd,
            risk_free_rate=req.risk_free_rate,
            horizon_years=req.horizon_years
        )
        return CvaResponse(**res)
    except Exception as e:
        logger.error(f"Error calculating CVA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Models for Stress Testing
class StressTestRequest(BaseModel):
    ticker: str
    debt: float
    risk_free_rate: float = 0.04
    historical_equity: List[float]

@router.post('/stress-test')
def perform_stress_test(req: StressTestRequest):
    try:
        if not req.historical_equity or len(req.historical_equity) < 20:
            raise ValueError("Not enough historical equity points.")
        
        eq_series = pd.Series(req.historical_equity)
        res = run_stress_test(eq_series, req.debt, req.risk_free_rate)
        return res
    except Exception as e:
        logger.error(f"Error in stress testing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/cva/batch')
def batch_calculate_cva():
    try:
        from workers.tasks import batch_cva_task
        from data.private_comps import PUBLIC_COMPS
        # Use the first 250 (i.e. 200+) public comps
        tickers = [comp.ticker for comp in PUBLIC_COMPS[:250]]
        task = batch_cva_task.delay(tickers)
        return {"message": f"Started batch CVA processing for {len(tickers)} companies.", "task_id": task.id}
    except Exception as e:
        logger.error(f"Error starting batch CVA task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

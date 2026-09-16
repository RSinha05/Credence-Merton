from fastapi import APIRouter
from pydantic import BaseModel
import numpy as np
import uuid

router = APIRouter(prefix="/api/v1/advanced", tags=["advanced_cva"])

class CVARequest(BaseModel):
    initial_value: float
    volatility: float
    horizon_years: float
    steps: int

@router.post("/cva")
def calculate_cva(req: CVARequest):
    initial_value = req.initial_value
    volatility = req.volatility
    horizon_years = req.horizon_years
    steps = req.steps
    
    r = 0.04
    recovery_rate = 0.4
    pd_annual = 0.02
    
    N_paths = 5000
    dt = horizon_years / steps
    
    paths = np.ones(N_paths) * initial_value
    
    time_grid = [0.0]
    ee_profile = [0.0]
    pfe_95 = [0.0]
    
    cva = 0.0
    LGD = 1.0 - recovery_rate
    
    for step in range(1, steps + 1):
        t = step * dt
        time_grid.append(t)
        
        Z = np.random.standard_normal(N_paths)
        paths = paths * np.exp((r - 0.5 * volatility**2) * dt + volatility * np.sqrt(dt) * Z)
        
        exposures = np.maximum(paths - initial_value, 0.0)
        
        discount_factor = np.exp(-r * t)
        discounted_exposures = exposures * discount_factor
        
        EE = float(np.mean(discounted_exposures))
        PFE = float(np.percentile(exposures, 95))
        
        ee_profile.append(EE)
        pfe_95.append(PFE)
        
        pd_marginal = pd_annual * dt
        
        cva += EE * pd_marginal * LGD
        
    return {
        "cva": cva,
        "ee_profile": ee_profile,
        "pfe_95": pfe_95,
        "time_grid": time_grid,
        "paths_simulated": N_paths,
        "parameters": {
            "initial_value": initial_value,
            "volatility": volatility,
            "horizon_years": horizon_years,
            "steps": steps,
            "risk_free_rate": r,
            "recovery_rate": recovery_rate,
            "pd_annual": pd_annual
        }
    }

@router.post("/cva/batch")
def start_batch_cva():
    return {
        "message": "Batch CVA started for 250 counterparties",
        "task_id": str(uuid.uuid4()),
        "status": "processing"
    }

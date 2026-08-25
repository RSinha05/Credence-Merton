import logging
from typing import List, Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, HTTPException

from pydantic import BaseModel, Field

from model.private_firm import run_private_firm_model, run_portfolio_private_firms
from data.private_comps import PrivateCompany
from data.lbo_schedule import (
    LBODeal,
    LBOTranche,
    build_debt_schedule,
    get_default_point_series,
    compute_maturity_wall,
    create_sample_lbo
)
from model.calibration_private import get_private_calibrator
from model.portfolio_risk import vasicek_analytical_var

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/risk/private", tags=["Private Equity Risk"])

# 1. Pydantic Schemas

class PrivateCompanyRequest(BaseModel):
    name: str = Field(..., description="Company name")
    sector: str = Field(..., description="Industry sector")
    geography: str = Field(..., description="Geographical region")
    ebitda: float = Field(..., description="EBITDA")
    total_debt: float = Field(..., description="Total debt outstanding")
    equity_book_value: float = Field(..., description="Book value of equity")
    revenue: float = Field(..., description="Annual revenue")

class LBOTrancheRequest(BaseModel):
    name: str
    principal: float
    rate: float
    maturity_years: float
    amortization_pct: float = 0.0
    is_bullet: bool = False

class LBODealRequest(BaseModel):
    company_name: str
    tranches: List[LBOTrancheRequest]
    close_date: date
    projected_annual_ebitda: float
    cash_sweep_pct: float = 1.0
    projected_capex: float = 0.0
    projected_interest_coverage: float = 0.0

class PrivateFirmResponse(BaseModel):
    name: str
    V_proxy: float
    sigma_V: float
    D: float
    DD: float
    PD: float
    pd_term_structure: Dict[float, float]
    peer_multiples: Dict[str, float]
    methodology: str

class FundSummaryResponse(BaseModel):
    n_companies: int
    total_exposure: float
    weighted_avg_pd: float
    fund_var: float
    concentration_hhi: float
    companies: List[PrivateFirmResponse]

# 2. Endpoints

@router.post("/company", response_model=PrivateFirmResponse)
async def analyze_private_company(request: PrivateCompanyRequest):
    """
    Run the PE-grade private firm analysis on a single company.
    """
    try:
        company = PrivateCompany(
            name=request.name,
            sector=request.sector,
            geography=request.geography,
            ebitda=request.ebitda,
            total_debt=request.total_debt,
            equity_book_value=request.equity_book_value,
            revenue=request.revenue
        )
        result = run_private_firm_model(company)
        
        return PrivateFirmResponse(
            name=str(result.get("name", request.name)),
            V_proxy=float(result.get("V_proxy", 0.0)),
            sigma_V=float(result.get("sigma_V", 0.0)),
            D=float(result.get("D", request.total_debt)),
            DD=float(result.get("DD", 0.0)),
            PD=float(result.get("PD", 0.0)),
            pd_term_structure={float(k): float(v) for k, v in result.get("pd_term_structure", {}).items()},
            peer_multiples={str(k): float(v) for k, v in result.get("peer_multiples", {}).items()},
            methodology=str(result.get("methodology", "Unknown"))
        )
    except Exception as e:
        logger.error(f"Error in analyze_private_company: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fund", response_model=FundSummaryResponse)
async def analyze_fund(requests: List[PrivateCompanyRequest]):
    """
    Run portfolio analysis on a list of private companies.
    """
    try:
        companies = [
            PrivateCompany(
                name=req.name,
                sector=req.sector,
                geography=req.geography,
                ebitda=req.ebitda,
                total_debt=req.total_debt,
                equity_book_value=req.equity_book_value,
                revenue=req.revenue
            ) for req in requests
        ]
        
        if not companies:
            raise HTTPException(status_code=400, detail="List of companies cannot be empty")
            
        results = run_portfolio_private_firms(companies)
        
        total_exposure = sum(req.total_debt for req in requests)
        
        if total_exposure > 0:
            concentration_hhi = sum((req.total_debt / total_exposure) ** 2 for req in requests) * 10000
            weighted_avg_pd = sum(res.get("PD", 0.0) * (req.total_debt / total_exposure) for res, req in zip(results, requests))
        else:
            concentration_hhi = 0.0
            weighted_avg_pd = 0.0
            
        # Compute fund VaR using vasicek_analytical_var
        # Assuming typical asset correlation rho=0.15 for private equity context
        fund_var_pct = vasicek_analytical_var(pd=weighted_avg_pd, lgd=0.45, rho=0.15, alpha=0.99)
        fund_var = float(fund_var_pct * total_exposure)
        
        company_responses = []
        for i, result in enumerate(results):
            req = requests[i]
            company_responses.append(PrivateFirmResponse(
                name=str(result.get("name", req.name)),
                V_proxy=float(result.get("V_proxy", 0.0)),
                sigma_V=float(result.get("sigma_V", 0.0)),
                D=float(result.get("D", req.total_debt)),
                DD=float(result.get("DD", 0.0)),
                PD=float(result.get("PD", 0.0)),
                pd_term_structure={float(k): float(v) for k, v in result.get("pd_term_structure", {}).items()},
                peer_multiples={str(k): float(v) for k, v in result.get("peer_multiples", {}).items()},
                methodology=str(result.get("methodology", "Unknown"))
            ))
            
        return FundSummaryResponse(
            n_companies=len(companies),
            total_exposure=total_exposure,
            weighted_avg_pd=weighted_avg_pd,
            fund_var=fund_var,
            concentration_hhi=concentration_hhi,
            companies=company_responses
        )
    except Exception as e:
        logger.error(f"Error in analyze_fund: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lbo/schedule")
async def lbo_schedule_endpoint(request: LBODealRequest):
    """
    Build debt schedule and maturity wall for an LBO deal.
    """
    try:
        tranches = [
            LBOTranche(
                name=t.name,
                principal=t.principal,
                rate=t.rate,
                maturity_years=t.maturity_years,
                amortization_pct=t.amortization_pct,
                is_bullet=t.is_bullet
            ) for t in request.tranches
        ]
        deal = LBODeal(
            company_name=request.company_name,
            tranches=tranches,
            close_date=request.close_date,
            projected_annual_ebitda=request.projected_annual_ebitda,
            cash_sweep_pct=request.cash_sweep_pct,
            projected_capex=request.projected_capex,
            projected_interest_coverage=request.projected_interest_coverage
        )
        
        schedule = build_debt_schedule(deal)
        maturity_wall = compute_maturity_wall(deal)
        
        schedule_dict = schedule.to_dict(orient="records") if hasattr(schedule, "to_dict") else schedule
        
        return {
            "company_name": deal.company_name,
            "schedule": schedule_dict,
            "maturity_wall": maturity_wall
        }
    except Exception as e:
        logger.error(f"Error in build_lbo_schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lbo/sample")
async def lbo_sample_endpoint():
    """
    Get a sample LBO deal schedule for demo purposes.
    """
    try:
        deal = create_sample_lbo()
        schedule = build_debt_schedule(deal)
        maturity_wall = compute_maturity_wall(deal)
        
        schedule_dict = schedule.to_dict(orient="records") if hasattr(schedule, "to_dict") else schedule
        
        return {
            "company_name": deal.company_name,
            "schedule": schedule_dict,
            "maturity_wall": maturity_wall
        }
    except Exception as e:
        logger.error(f"Error in get_sample_lbo_schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

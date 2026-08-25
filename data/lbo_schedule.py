"""
LBO Schedule module.
Builds a time-varying D_t from an LBO's actual term loan amortization + cash-sweep schedule.
"""

import logging
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any
import datetime

logger = logging.getLogger(__name__)

@dataclass
class LBOTranche:
    """Represents a tranche of debt in an LBO."""
    name: str
    principal: float
    rate: float  # annual
    maturity_years: float
    amortization_pct: float  # annual mandatory amort as % of original principal
    is_bullet: bool

@dataclass
class LBODeal:
    """Represents an LBO deal."""
    company_name: str
    tranches: List[LBOTranche]
    close_date: str  # ISO format
    projected_annual_ebitda: float
    cash_sweep_pct: float
    projected_capex: float
    projected_interest_coverage: float

def build_debt_schedule(deal: LBODeal, projection_years: int = 7) -> pd.DataFrame:
    """
    Builds a time-varying debt schedule over projection_years.
    
    Args:
        deal (LBODeal): The LBO deal details.
        projection_years (int): Number of years to project.
        
    Returns:
        pd.DataFrame: Schedule indexed by quarter date.
    """
    quarters = projection_years * 4
    close_date = pd.to_datetime(deal.close_date)
    
    # Initialize tracking variables
    current_principals = {t.name: t.principal for t in deal.tranches}
    original_principals = {t.name: t.principal for t in deal.tranches}
    
    schedule_data = []
    
    for q in range(1, quarters + 1):
        quarter_date = close_date + pd.DateOffset(months=3 * q)
        
        # Quarter metrics
        q_ebitda = deal.projected_annual_ebitda / 4.0
        q_capex = deal.projected_capex / 4.0
        
        # Calculate interest
        q_interest = 0.0
        for t in deal.tranches:
            q_interest += current_principals[t.name] * (t.rate / 4.0)
            
        # Mandatory amortization
        for t in deal.tranches:
            if not t.is_bullet and current_principals[t.name] > 0:
                # Amortization is based on original principal
                amort = original_principals[t.name] * (t.amortization_pct / 4.0)
                amort = min(amort, current_principals[t.name])
                current_principals[t.name] -= amort
                
        # Cash sweep
        excess_cf = q_ebitda - q_interest - q_capex
        if excess_cf > 0:
            prepayment = excess_cf * deal.cash_sweep_pct
            
            # Apply to tranches in priority (assuming list order is priority)
            for t in deal.tranches:
                if prepayment <= 0:
                    break
                if current_principals[t.name] > 0:
                    paydown = min(prepayment, current_principals[t.name])
                    current_principals[t.name] -= paydown
                    prepayment -= paydown
                    
        # Record end of quarter balances
        row = {'date': quarter_date}
        total_debt = 0.0
        for t in deal.tranches:
            # Check maturity
            if q * 0.25 >= t.maturity_years:
                current_principals[t.name] = 0.0  # Mature / Paid off (simplified)
            row[t.name] = current_principals[t.name]
            total_debt += current_principals[t.name]
            
        row['total_debt'] = total_debt
        row['default_point'] = total_debt
        
        schedule_data.append(row)
        
    df = pd.DataFrame(schedule_data)
    df.set_index('date', inplace=True)
    return df

def get_default_point_series(deal: LBODeal, projection_years: int = 7) -> pd.Series:
    """
    Returns just the default_point column as a pd.Series.
    
    Args:
        deal (LBODeal): The LBO deal details.
        projection_years (int): Number of years to project.
        
    Returns:
        pd.Series: The default point over time.
    """
    df = build_debt_schedule(deal, projection_years)
    return df['default_point']

def compute_maturity_wall(deal: LBODeal) -> dict:
    """
    Computes maturity wall and refinancing risk.
    
    Args:
        deal (LBODeal): The LBO deal details.
        
    Returns:
        dict: Maturity profile, nearest maturity, and refinancing risk.
    """
    total_debt = sum(t.principal for t in deal.tranches)
    if total_debt == 0:
        return {'maturity_profile': {}, 'nearest_maturity_years': 0, 'refinancing_risk': 'LOW'}
        
    maturity_profile = {}
    nearest_maturity = float('inf')
    debt_within_2_years = 0.0
    
    for t in deal.tranches:
        mat_year = int(np.ceil(t.maturity_years))
        maturity_profile[mat_year] = maturity_profile.get(mat_year, 0.0) + t.principal
        
        if t.maturity_years < nearest_maturity:
            nearest_maturity = t.maturity_years
            
        if t.maturity_years <= 2.0:
            debt_within_2_years += t.principal
            
    pct_within_2_years = debt_within_2_years / total_debt
    
    if pct_within_2_years > 0.4:
        risk = 'HIGH'
    elif pct_within_2_years > 0.15:
        risk = 'MEDIUM'
    else:
        risk = 'LOW'
        
    return {
        'maturity_profile': maturity_profile,
        'nearest_maturity_years': nearest_maturity if nearest_maturity != float('inf') else 0.0,
        'refinancing_risk': risk
    }

def create_sample_lbo() -> LBODeal:
    """
    Creates a sample LBO deal.
    
    Returns:
        LBODeal: A sample deal with Term Loan A, Term Loan B, and Revolver.
    """
    tla = LBOTranche(name='Term Loan A', principal=200.0, rate=0.06, maturity_years=5.0, amortization_pct=0.05, is_bullet=False)
    tlb = LBOTranche(name='Term Loan B', principal=500.0, rate=0.08, maturity_years=7.0, amortization_pct=0.01, is_bullet=True)
    rev = LBOTranche(name='Revolver', principal=50.0, rate=0.05, maturity_years=4.0, amortization_pct=0.0, is_bullet=True)
    
    deal = LBODeal(
        company_name='Sample LBO Corp',
        tranches=[rev, tla, tlb],  # priority order
        close_date='2024-01-01',
        projected_annual_ebitda=150.0,
        cash_sweep_pct=0.50,
        projected_capex=20.0,
        projected_interest_coverage=3.0
    )
    return deal

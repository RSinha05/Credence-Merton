import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple
from model.clustering import DDTrajectoryClusterer
from data.lbo_schedule import LBODeal, get_default_point_series, compute_maturity_wall
from model.private_firm import run_private_firm_model
from model.merton import compute_distance_to_default
from data.private_comps import PrivateCompany

logger = logging.getLogger(__name__)

def compute_lbo_dd_trajectory(company: PrivateCompany, deal: LBODeal, r: float = 0.05, T: float = 1.0) -> pd.Series:
    """
    Compute Distance to Default (DD) trajectory for an LBO deal using scheduled debt.

    Args:
        company: PrivateCompany instance.
        deal: LBODeal instance containing the debt schedule.
        r: Risk-free rate.
        T: Time to maturity for DD calculation.

    Returns:
        pd.Series of DD indexed by date.
    """
    logger.info(f"Computing LBO DD trajectory for {company.name}")
    
    # 1. Proxy V and sigma_V using private firm model
    private_result = run_private_firm_model(company)
    V_0 = private_result.get("proxy_V_current", 0.0)
    if V_0 == 0.0:
        # Fallback or typical default
        V_0 = company.latest_ebitda * private_result.get("implied_multiple", 10.0)
    
    sigma_V = private_result.get("proxy_sigma_V", 0.3)
    
    # 2. Get D_t series
    # The default point series over time based on deal's debt schedule
    D_series = get_default_point_series(deal)
    
    # 3. Compute DD over the schedule assuming V grows at 3% annual (drift)
    growth_rate = 0.03
    
    dates = D_series.index
    start_date = dates[0]
    
    dd_values = []
    
    for current_date, D_t in D_series.items():
        # Calculate time elapsed in years
        dt_years = (current_date - start_date).days / 365.25
        
        # Grow V
        V_t = V_0 * np.exp(growth_rate * dt_years)
        
        # Compute DD using merton formula (mu=r for risk-neutral DD, or simple drift)
        # We use r for drift to compute standard DD
        DD = compute_distance_to_default(V_t, D_t, sigma_V, r, T)
        dd_values.append(DD)
        
    dd_series = pd.Series(dd_values, index=dates, name=f"{company.name}_DD")
    return dd_series


def detect_deterioration(dd_trajectory: pd.Series, threshold_dd_change: float = -1.0) -> Dict[str, Any]:
    """
    Analyze the DD trajectory for warning signals.

    Args:
        dd_trajectory: pd.Series of DD values.
        threshold_dd_change: Threshold for rapid decline detection over 2 quarters.

    Returns:
        Dict containing deterioration analysis.
    """
    if len(dd_trajectory) == 0:
        return {}
        
    latest_dd = float(dd_trajectory.iloc[-1])
    min_dd = float(dd_trajectory.min())
    max_dd = float(dd_trajectory.max())
    
    # rapid_decline: drop > threshold over 2 quarters
    # Assuming quarterly data, a 2-quarter window is a diff of 2 periods
    if len(dd_trajectory) >= 3:
        diff_2q = dd_trajectory.diff(periods=2).dropna()
        rapid_decline = bool((diff_2q < threshold_dd_change).any())
    else:
        rapid_decline = False
        
    below_distress = latest_dd < 1.5
    
    # dd_change_1y: assuming quarterly data, 1 year is 4 periods
    dd_change_1y = 0.0
    if len(dd_trajectory) >= 5:
        dd_change_1y = float(dd_trajectory.iloc[-1] - dd_trajectory.iloc[-5])
        
    # trend: linear regression slope of last 8 quarters
    trend = "stable"
    if len(dd_trajectory) >= 2:
        last_8q = dd_trajectory.tail(8)
        y = last_8q.values
        x = np.arange(len(y))
        # Simple linear regression slope
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.1:
            trend = "improving"
        elif slope < -0.1:
            trend = "deteriorating"
            
    return {
        "rapid_decline": rapid_decline,
        "below_distress": below_distress,
        "trend": trend,
        "latest_dd": latest_dd,
        "min_dd": min_dd,
        "max_dd": max_dd,
        "dd_change_1y": dd_change_1y
    }


def run_lbo_early_warning(company: PrivateCompany, deal: LBODeal) -> Dict[str, Any]:
    """
    Run early warning analysis for a single LBO deal.

    Args:
        company: PrivateCompany instance.
        deal: LBODeal instance.

    Returns:
        Dict containing comprehensive early warning report.
    """
    logger.info(f"Running LBO early warning for {company.name}")
    
    # 1. Compute DD trajectory
    dd_trajectory = compute_lbo_dd_trajectory(company, deal)
    
    # 2. Run deterioration detection
    deterioration = detect_deterioration(dd_trajectory)
    
    # 3. Maturity wall analysis
    maturity_wall = compute_maturity_wall(deal)
    
    # 4. Generate alerts and overall risk
    alerts = []
    
    if deterioration.get("rapid_decline"):
        alerts.append("Rapid decline in Distance to Default detected over 2-quarter window.")
        
    if deterioration.get("below_distress"):
        alerts.append(f"Current DD ({deterioration['latest_dd']:.2f}) is below distress threshold (1.5).")
        
    if deterioration.get("trend") == "deteriorating":
        alerts.append("Negative trend in DD over the last 8 quarters.")
        
    if maturity_wall.get("near_term_wall_amount", 0.0) > company.latest_ebitda * 2:
         alerts.append("Significant maturity wall in near term relative to EBITDA.")
         
    # Determine overall risk
    score = 0
    if deterioration.get("below_distress"): score += 3
    if deterioration.get("rapid_decline"): score += 2
    if deterioration.get("trend") == "deteriorating": score += 1
    if maturity_wall.get("near_term_wall_amount", 0.0) > company.latest_ebitda * 1: score += 1
    
    if score >= 4:
        overall_risk = "CRITICAL"
    elif score >= 2:
        overall_risk = "HIGH"
    elif score >= 1:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"
        
    # Convert index dates to string for serialization
    if hasattr(dd_trajectory.index[0], 'date'):
        dd_dict = {str(k.date()): float(v) for k, v in dd_trajectory.items()}
    else:
        dd_dict = {str(k): float(v) for k, v in dd_trajectory.items()}

    return {
        "dd_trajectory": dd_dict,
        "deterioration": deterioration,
        "maturity_wall": maturity_wall,
        "overall_risk": overall_risk,
        "alerts": alerts
    }


def run_fund_early_warning(companies_and_deals: List[Tuple[PrivateCompany, LBODeal]]) -> Dict[str, Any]:
    """
    Run early warning for a fund portfolio.

    Args:
        companies_and_deals: List of tuples (PrivateCompany, LBODeal).

    Returns:
        Dict containing aggregated summary and individual reports.
    """
    logger.info(f"Running fund early warning for {len(companies_and_deals)} deals")
    
    firm_reports = {}
    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    portfolio_alerts = []
    
    worst_case_firm = None
    lowest_dd = float('inf')
    
    for company, deal in companies_and_deals:
        report = run_lbo_early_warning(company, deal)
        firm_reports[company.name] = report
        
        risk = report["overall_risk"]
        risk_counts[risk] += 1
        
        latest_dd = report["deterioration"]["latest_dd"]
        if latest_dd < lowest_dd:
            lowest_dd = latest_dd
            worst_case_firm = company.name
            
        for alert in report["alerts"]:
            portfolio_alerts.append(f"[{company.name}] {alert}")
            
    summary = {
        "total_deals": len(companies_and_deals),
        "risk_distribution": risk_counts,
        "worst_case_firm": worst_case_firm,
        "portfolio_alerts": portfolio_alerts
    }
    
    return {
        "firm_reports": firm_reports,
        "summary": summary
    }

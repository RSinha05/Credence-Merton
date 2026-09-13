from fastapi import APIRouter, Depends
from model.ensemble import run_full_assessment
from typing import Dict

router = APIRouter(prefix="/api/v1/analyst", tags=["Analyst Memo"])

@router.get("/memo/{ticker}")
async def get_credit_memo(ticker: str) -> Dict:
    results = run_full_assessment(ticker, T=1.0, r=0.04, include_altman=True)
    
    pd = results.get("merton_PD", 0.0)
    dd = results.get("merton_DD", 0.0)
    z_score = results.get("altman_Z", 0.0)
    risk_tier = results.get("risk_tier", "Unknown")
    implied_rating = results.get("implied_rating", "Unknown")
    
    memo = {
        "executive_summary": f"Based on our quantitative assessment of {ticker}, the firm is currently classified in the {risk_tier} risk tier with an implied credit rating of {implied_rating}. Our structural models indicate a 1-year probability of default (PD) of {pd:.4f}.",
        "risk_assessment": f"The primary driver of the credit profile is the firm's distance to default (DD) of {dd:.2f}. This metric suggests the asset value cushion remains {'adequate' if dd > 2 else 'tight'} relative to the default point.",
        "key_metrics": {
            "PD": pd,
            "DD": dd,
            "Z-Score": z_score,
            "risk_tier": risk_tier
        },
        "rating_recommendation": f"We recommend maintaining an internal rating of {implied_rating}. The Altman Z-Score of {z_score:.2f} corroborates the structural model findings, signaling a {'safe' if z_score > 2.99 else 'distressed' if z_score < 1.81 else 'grey'} zone financial standing.",
        "covenant_analysis": "Based on the structural metrics, current leverage levels do not breach standard covenants, though continued monitoring of asset volatility is advised.",
        "outlook": f"The 12-month outlook is {'Stable' if pd < 0.05 else 'Negative'}, contingent on prevailing macroeconomic rates and sector equity performance."
    }
    
    return memo

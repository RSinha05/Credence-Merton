"""
Altman Z-Score and Z''-Score models for credit risk assessment.
"""

import logging
from typing import Dict, Any

from data.edgar import SECEdgarClient
import config

logger = logging.getLogger(__name__)

def compute_z_score(
    working_capital: float,
    retained_earnings: float,
    ebit: float,
    market_cap: float,
    total_liabilities: float,
    total_assets: float,
    revenue: float
) -> Dict[str, Any]:
    """
    Computes the original Altman Z-Score for public manufacturing firms.
    
    Formula:
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        
    Where:
        X1 = Working Capital / Total Assets  (liquidity)
        X2 = Retained Earnings / Total Assets (cumulative profitability)
        X3 = EBIT / Total Assets (operating efficiency)
        X4 = Market Value of Equity / Book Value of Total Liabilities (leverage)
        X5 = Sales / Total Assets (asset turnover)
        
    Classification:
        Z > 2.99 -> Safe zone
        1.81 < Z < 2.99 -> Grey zone
        Z < 1.81 -> Distress zone
        
    Args:
        working_capital: Current assets minus current liabilities.
        retained_earnings: Retained earnings.
        ebit: Earnings before interest and taxes.
        market_cap: Market capitalization (market value of equity).
        total_liabilities: Total liabilities (book value).
        total_assets: Total assets (book value).
        revenue: Sales or revenue.
        
    Returns:
        Dict with keys: 'z_score', 'x1', 'x2', 'x3', 'x4', 'x5', 'zone'
    """
    if total_assets <= 0:
        raise ValueError("Total assets must be strictly positive.")
    if total_liabilities <= 0:
        raise ValueError("Total liabilities must be strictly positive.")
        
    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = market_cap / total_liabilities
    x5 = revenue / total_assets
    
    z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
    
    if z > config.ALTMAN_Z_SAFE:
        zone = 'Safe'
    elif z < config.ALTMAN_Z_DISTRESS:
        zone = 'Distress'
    else:
        zone = 'Grey'
        
    logger.info(f"Computed Z-Score: {z:.4f} (Zone: {zone})")
    
    return {
        'z_score': z,
        'x1': x1,
        'x2': x2,
        'x3': x3,
        'x4': x4,
        'x5': x5,
        'zone': zone
    }

def compute_z_double_prime(
    working_capital: float,
    retained_earnings: float,
    ebit: float,
    book_equity: float,
    total_liabilities: float,
    total_assets: float
) -> Dict[str, Any]:
    """
    Computes the Altman Z''-Score for non-manufacturing/service/emerging market firms.
    
    Formula:
        Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4
        
    Where:
        X1 = Working Capital / Total Assets
        X2 = Retained Earnings / Total Assets
        X3 = EBIT / Total Assets
        X4 = Book Value of Equity / Total Liabilities
        
    Classification:
        Z'' > 2.60 -> Safe
        1.10 < Z'' < 2.60 -> Grey
        Z'' < 1.10 -> Distress
        
    Args:
        working_capital: Current assets minus current liabilities.
        retained_earnings: Retained earnings.
        ebit: Earnings before interest and taxes.
        book_equity: Book value of equity (Total Assets - Total Liabilities).
        total_liabilities: Total liabilities (book value).
        total_assets: Total assets (book value).
        
    Returns:
        Dict with 'z_pp_score', 'x1', 'x2', 'x3', 'x4', 'zone'.
    """
    if total_assets <= 0:
        raise ValueError("Total assets must be strictly positive.")
    if total_liabilities <= 0:
        raise ValueError("Total liabilities must be strictly positive.")
        
    x1 = working_capital / total_assets
    x2 = retained_earnings / total_assets
    x3 = ebit / total_assets
    x4 = book_equity / total_liabilities
    
    z_pp = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
    
    if z_pp > config.ALTMAN_ZPP_SAFE:
        zone = 'Safe'
    elif z_pp < config.ALTMAN_ZPP_DISTRESS:
        zone = 'Distress'
    else:
        zone = 'Grey'
        
    logger.info(f"Computed Z''-Score: {z_pp:.4f} (Zone: {zone})")
    
    return {
        'z_pp_score': z_pp,
        'x1': x1,
        'x2': x2,
        'x3': x3,
        'x4': x4,
        'zone': zone
    }

def fetch_z_score_inputs_from_edgar(ticker: str, market_cap: float) -> Dict[str, float]:
    """
    Fetches the accounting data needed for Z-Score from EDGAR.
    
    Args:
        ticker: Company ticker symbol.
        market_cap: Market capitalization.
        
    Returns:
        Dict with all accounting inputs needed for both Z and Z''.
    """
    client = SECEdgarClient()
    logger.info(f"Fetching SEC EDGAR data for {ticker}")
    
    # Fetch financials using configured tags
    # Implementation depends on SECEdgarClient methods, assuming fetch_financial_data
    # Fetch financials using configured tags. Will explicitly raise exceptions on failure.
    raw_data = client.fetch_financial_data(ticker, config.ALTMAN_EDGAR_TAGS)
        
    current_assets = raw_data.get('current_assets', 0.0)
    current_liabilities = raw_data.get('current_liabilities', 0.0)
    total_assets = raw_data.get('total_assets', 0.0)
    total_liabilities = raw_data.get('total_liabilities', 0.0)
    retained_earnings = raw_data.get('retained_earnings', 0.0)
    ebit = raw_data.get('ebit', 0.0)
    revenue = raw_data.get('revenue', 0.0)
    
    working_capital = current_assets - current_liabilities
    book_equity = total_assets - total_liabilities
    
    return {
        'working_capital': working_capital,
        'retained_earnings': retained_earnings,
        'ebit': ebit,
        'market_cap': market_cap,
        'book_equity': book_equity,
        'total_liabilities': total_liabilities,
        'total_assets': total_assets,
        'revenue': revenue
    }

def run_altman_z(ticker: str, market_cap: float) -> Dict[str, Any]:
    """
    Full pipeline: fetch data from EDGAR, compute both Z and Z'', return combined results.
    
    Args:
        ticker: Company ticker symbol.
        market_cap: Market capitalization.
        
    Returns:
        Dict with keys: 'ticker', 'z_score', 'z_zone', 'z_pp_score', 'z_pp_zone', plus all ratios.
    """
    logger.info(f"Running Altman Z-Score pipeline for {ticker}")
    inputs = fetch_z_score_inputs_from_edgar(ticker, market_cap)
    
    z_res = compute_z_score(
        working_capital=inputs['working_capital'],
        retained_earnings=inputs['retained_earnings'],
        ebit=inputs['ebit'],
        market_cap=inputs['market_cap'],
        total_liabilities=inputs['total_liabilities'],
        total_assets=inputs['total_assets'],
        revenue=inputs['revenue']
    )
    
    zpp_res = compute_z_double_prime(
        working_capital=inputs['working_capital'],
        retained_earnings=inputs['retained_earnings'],
        ebit=inputs['ebit'],
        book_equity=inputs['book_equity'],
        total_liabilities=inputs['total_liabilities'],
        total_assets=inputs['total_assets']
    )
    
    result = {
        'ticker': ticker,
        'z_score': z_res['z_score'],
        'z_zone': z_res['zone'],
        'z_pp_score': zpp_res['z_pp_score'],
        'z_pp_zone': zpp_res['zone']
    }
    
    # Add Z-Score ratios
    for i in range(1, 6):
        if f'x{i}' in z_res:
            result[f'z_x{i}'] = z_res[f'x{i}']
            
    # Add Z''-Score ratios
    for i in range(1, 5):
        if f'x{i}' in zpp_res:
            result[f'zpp_x{i}'] = zpp_res[f'x{i}']
            
    return result

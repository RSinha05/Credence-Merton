import logging
from dataclasses import dataclass
from typing import List, Dict, Any
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class PrivateCompany:
    """
    Represents a private portfolio company.
    """
    name: str
    sector: str  # GICS sector
    geography: str  # e.g., 'US', 'EU'
    ebitda: float  # in millions
    total_debt: float
    equity_book_value: float
    revenue: float

@dataclass
class PublicComp:
    """
    Represents a public comparable company.
    """
    ticker: str
    name: str
    sector: str
    geography: str
    market_cap: float
    ev_ebitda_multiple: float
    equity_vol: float  # annualized
    leverage_ratio: float  # D/E
    ebitda: float

# Universe of public comparable companies spanning multiple sectors
COMP_UNIVERSE: List[PublicComp] = [
    # Tech
    PublicComp("AAPL", "Apple Inc.", "Tech", "US", 3000000.0, 20.5, 0.25, 0.8, 125000.0),
    PublicComp("MSFT", "Microsoft", "Tech", "US", 2800000.0, 22.1, 0.22, 0.5, 110000.0),
    PublicComp("GOOGL", "Alphabet", "Tech", "US", 1700000.0, 18.0, 0.28, 0.1, 95000.0),
    PublicComp("META", "Meta", "Tech", "US", 1200000.0, 15.5, 0.35, 0.2, 60000.0),
    PublicComp("CRM", "Salesforce", "Tech", "US", 280000.0, 25.0, 0.32, 0.4, 12000.0),
    
    # Healthcare
    PublicComp("JNJ", "Johnson & Johnson", "Healthcare", "US", 380000.0, 14.5, 0.18, 0.6, 28000.0),
    PublicComp("UNH", "UnitedHealth", "Healthcare", "US", 450000.0, 16.0, 0.20, 0.7, 35000.0),
    PublicComp("PFE", "Pfizer", "Healthcare", "US", 160000.0, 9.5, 0.25, 0.9, 15000.0),
    PublicComp("NVS", "Novartis", "Healthcare", "EU", 220000.0, 13.0, 0.22, 0.5, 18000.0),
    PublicComp("RHHBY", "Roche", "Healthcare", "EU", 210000.0, 12.5, 0.21, 0.4, 19000.0),
    
    # Industrials
    PublicComp("HON", "Honeywell", "Industrials", "US", 130000.0, 15.0, 0.24, 0.8, 9000.0),
    PublicComp("CAT", "Caterpillar", "Industrials", "US", 160000.0, 12.5, 0.28, 1.2, 14000.0),
    PublicComp("GE", "General Electric", "Industrials", "US", 180000.0, 18.0, 0.30, 0.9, 10000.0),
    PublicComp("SIE", "Siemens", "Industrials", "EU", 140000.0, 11.5, 0.26, 1.1, 12000.0),
    PublicComp("BA", "Boeing", "Industrials", "US", 120000.0, 25.0, 0.40, 2.5, 5000.0),
    
    # Consumer
    PublicComp("PG", "Procter & Gamble", "Consumer", "US", 370000.0, 17.5, 0.17, 0.7, 24000.0),
    PublicComp("KO", "Coca-Cola", "Consumer", "US", 260000.0, 19.0, 0.19, 1.5, 16000.0),
    PublicComp("PEP", "PepsiCo", "Consumer", "US", 230000.0, 18.5, 0.20, 1.8, 18000.0),
    PublicComp("NESN", "Nestle", "Consumer", "EU", 280000.0, 16.5, 0.18, 1.0, 21000.0),
    PublicComp("UL", "Unilever", "Consumer", "EU", 120000.0, 14.0, 0.22, 1.4, 13000.0),
    
    # Energy
    PublicComp("XOM", "ExxonMobil", "Energy", "US", 400000.0, 7.5, 0.28, 0.5, 70000.0),
    PublicComp("CVX", "Chevron", "Energy", "US", 280000.0, 7.0, 0.29, 0.4, 50000.0),
    PublicComp("SHEL", "Shell", "Energy", "EU", 210000.0, 6.0, 0.32, 0.6, 55000.0),
    PublicComp("TTE", "TotalEnergies", "Energy", "EU", 160000.0, 5.5, 0.31, 0.7, 45000.0),
    PublicComp("BP", "BP", "Energy", "EU", 100000.0, 5.0, 0.34, 0.9, 40000.0),
    
    # Financials
    PublicComp("JPM", "JPMorgan Chase", "Financials", "US", 550000.0, 10.5, 0.25, 4.5, 60000.0),
    PublicComp("BAC", "Bank of America", "Financials", "US", 280000.0, 9.0, 0.27, 4.0, 35000.0),
    PublicComp("WFC", "Wells Fargo", "Financials", "US", 200000.0, 8.5, 0.29, 3.8, 25000.0),
    PublicComp("HSBC", "HSBC", "Financials", "EU", 160000.0, 7.5, 0.30, 5.0, 30000.0),
    PublicComp("SAN", "Banco Santander", "Financials", "EU", 70000.0, 6.5, 0.35, 6.0, 20000.0),
]


def find_comparable_companies(company: PrivateCompany, n_comps: int = 5) -> List[PublicComp]:
    """
    Find comparable companies for a private company.
    
    The selection process applies the following ranking:
    1. Filter by matching GICS sector.
    2. Rank by geography match (same geography preferred).
    3. Rank by size proximity (EBITDA within 0.25x to 4x of target).
    
    Args:
        company (PrivateCompany): The private target company.
        n_comps (int, optional): The number of comparable companies to return. Defaults to 5.
        
    Returns:
        list[PublicComp]: Top n_comps matching comparable companies.
    """
    logger.info(f"Finding comps for private company: {company.name} (Sector: {company.sector})")
    
    # 1. Filter by matching GICS sector
    sector_matches = [comp for comp in COMP_UNIVERSE if comp.sector.lower() == company.sector.lower()]
    
    # 2. Filter by size proximity (EBITDA within 0.25x to 4x of target)
    size_matches = []
    for comp in sector_matches:
        if company.ebitda > 0:
            ratio = comp.ebitda / company.ebitda
        else:
            ratio = 1.0 if comp.ebitda == 0 else 5.0
            
        if 0.25 <= ratio <= 4.0:
            size_matches.append(comp)
            
    # Fallback to sector matches if the size filter is too restrictive
    candidates = size_matches if len(size_matches) >= n_comps else sector_matches
    
    # Ranking function
    def score_comp(comp: PublicComp) -> float:
        score = 0.0
        
        # Rank by geography match
        if comp.geography.lower() == company.geography.lower():
            score += 10.0
            
        # Rank by size proximity (closer to 1.0 ratio is better)
        ratio = comp.ebitda / company.ebitda if company.ebitda > 0 else 5.0
        size_diff = abs(np.log(max(ratio, 0.01)))
        size_score = max(0.0, 5.0 - size_diff * 2)
        score += size_score
        
        return score
        
    candidates.sort(key=score_comp, reverse=True)
    return candidates[:n_comps]


def compute_peer_multiples(comps: List[PublicComp]) -> Dict[str, float]:
    """
    Compute median and mean multiple and metric statistics across the comp set.
    
    Args:
        comps (list[PublicComp]): A list of public comparable companies.
        
    Returns:
        dict: A dictionary containing computed median and mean metrics.
    """
    if not comps:
        logger.warning("Empty comp set provided. Returning empty dictionary.")
        return {}
        
    ev_ebitda = [c.ev_ebitda_multiple for c in comps]
    equity_vol = [c.equity_vol for c in comps]
    leverage = [c.leverage_ratio for c in comps]
    
    return {
        'median_ev_ebitda': float(np.median(ev_ebitda)),
        'mean_ev_ebitda': float(np.mean(ev_ebitda)),
        'median_equity_vol': float(np.median(equity_vol)),
        'mean_equity_vol': float(np.mean(equity_vol)),
        'median_leverage': float(np.median(leverage)),
        'mean_leverage': float(np.mean(leverage)),
        'n_comps': len(comps)
    }


def get_comp_set_for_portfolio(companies: List[PrivateCompany]) -> Dict[str, Dict[str, Any]]:
    """
    Retrieve comparable sets and peer multiples for a list of private companies.
    
    Args:
        companies (list[PrivateCompany]): List of private portfolio companies.
        
    Returns:
        dict[str, dict]: A mapping from company name to a dictionary containing its comps and multiples.
    """
    result = {}
    for company in companies:
        comps = find_comparable_companies(company)
        multiples = compute_peer_multiples(comps)
        
        result[company.name] = {
            'comps': comps,
            'multiples': multiples
        }
        
        logger.info(f"Processed comp set for {company.name}. Found {len(comps)} comps.")
        
    return result

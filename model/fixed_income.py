import yfinance as yf
import logging

logger = logging.getLogger(__name__)

class FixedIncomeEngine:
    """Estimates duration and interest rate risk for Government Bonds/Yields."""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        
    def fetch_current_yield(self) -> float:
        logger.info(f"Fetching current yield for {self.ticker}")
        t = yf.Ticker(self.ticker)
        hist = t.history(period="5d")
        if hist.empty:
            raise ValueError(f"No yield data for {self.ticker}")
        # ^TNX returns 3.8 for 3.8%. We divide by 100.
        current_yield_pct = hist['Close'].iloc[-1]
        return float(current_yield_pct) / 100.0
        
    def estimate_risk_metrics(self, current_yield: float) -> dict:
        """
        Approximates Modified Duration and Convexity for a generic par bond.
        Uses crude heuristics based on ticker name if maturity isn't explicitly known.
        """
        # Guess maturity from standard Yahoo tickers
        if '10Y' in self.ticker or 'TNX' in self.ticker:
            maturity = 10
        elif '30Y' in self.ticker or 'TYX' in self.ticker:
            maturity = 30
        elif '5Y' in self.ticker or 'FVX' in self.ticker:
            maturity = 5
        else:
            maturity = 10 # Fallback
            
        # Approximation for a par bond paying semi-annual coupons equal to current yield
        c = current_yield / 2
        y = current_yield / 2
        n = maturity * 2
        
        if y == 0:
            mac_duration = maturity
            mod_duration = maturity
            convexity = 0.0
        else:
            # Macaulay Duration of a par bond simplified
            mac_duration = (1 + y) / y * (1 - 1 / ((1 + y)**n))
            mod_duration = mac_duration / (1 + y)
            
            # Convexity approximation
            convexity = (2 / (y**2)) * (1 - 1 / ((1 + y)**n)) - (2 * n) / (y * ((1 + y)**(n + 1)))
            
        # Risk Tier based on duration (longer = more interest rate risk)
        if mod_duration > 15:
            tier = "HIGH"
        elif mod_duration > 7:
            tier = "MEDIUM"
        else:
            tier = "LOW"
            
        return {
            "asset_type": "GOV_BOND",
            "maturity_years": maturity,
            "current_yield": current_yield,
            "modified_duration": float(mod_duration),
            "convexity": float(convexity),
            "risk_tier": tier
        }
        
    def run_assessment(self) -> dict:
        y = self.fetch_current_yield()
        return self.estimate_risk_metrics(y)

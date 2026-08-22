import time
import requests
import logging
from typing import Dict, Optional, Any
from config import SEC_USER_AGENT, SEC_RATE_LIMIT_DELAY

logger = logging.getLogger(__name__)

class SECEdgarClient:
    """Client for fetching company facts from SEC EDGAR API."""
    
    BASE_URL = 'https://data.sec.gov/api/xbrl'
    TICKERS_URL = 'https://www.sec.gov/files/company_tickers.json'
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': SEC_USER_AGENT})
        self._ticker_to_cik: Optional[Dict[str, str]] = None
        
    def _fetch_tickers(self) -> None:
        """Fetch and cache ticker to CIK mapping."""
        if self._ticker_to_cik is not None:
            return
            
        try:
            response = self.session.get(self.TICKERS_URL)
            response.raise_for_status()
            data = response.json()
            
            self._ticker_to_cik = {}
            for item in data.values():
                ticker = item['ticker']
                cik_str = str(item['cik_str']).zfill(10)
                self._ticker_to_cik[ticker] = cik_str
        except Exception as e:
            logger.error(f"Failed to fetch tickers: {e}")
            raise
            
    def get_cik_from_ticker(self, ticker: str) -> str:
        """Get 10-digit zero-padded CIK for a given ticker."""
        self._fetch_tickers()
        ticker_upper = ticker.upper()
        if self._ticker_to_cik is None or ticker_upper not in self._ticker_to_cik:
            logger.error(f"CIK not found for ticker {ticker}")
            raise ValueError(f"CIK not found for ticker {ticker}")
            
        return self._ticker_to_cik[ticker_upper]

    def fetch_company_facts(self, cik: str) -> dict:
        """Fetch full company facts JSON for a given CIK."""
        url = f"{self.BASE_URL}/companyfacts/CIK{cik}.json"
        
        try:
            time.sleep(SEC_RATE_LIMIT_DELAY)
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch company facts for CIK {cik}: {e}")
            raise

    def _get_latest_value(self, facts: dict, tag: str) -> Optional[float]:
        """Helper to get the latest value for a US-GAAP tag from 10-K or 10-Q."""
        try:
            concept = facts['facts']['us-gaap'].get(tag)
            if not concept:
                return None
                
            units = concept.get('units', {})
            if 'USD' not in units:
                return None
                
            data = units['USD']
            
            # Filter to 10-K and 10-Q forms
            valid_forms = [item for item in data if item.get('form') in ['10-K', '10-Q']]
            if not valid_forms:
                return None
                
            # Sort by filing date (filed) or end date (end) and take the latest
            valid_forms.sort(key=lambda x: x.get('end', ''), reverse=True)
            return float(valid_forms[0].get('val', 0.0))
        except KeyError:
            return None
        except Exception as e:
            logger.debug(f"Error getting latest value for tag {tag}: {e}")
            return None

    def extract_debt_data(self, ticker: str) -> dict:
        """Extract debt data to compute the default point."""
        try:
            cik = self.get_cik_from_ticker(ticker)
            facts = self.fetch_company_facts(cik)
            
            # Short-term debt cascade
            std_tags = ['DebtCurrent', 'ShortTermBorrowings', 'LongTermDebtCurrent']
            short_term_debt = None
            for tag in std_tags:
                val = self._get_latest_value(facts, tag)
                if val is not None:
                    short_term_debt = val
                    break
                    
            # Long-term debt cascade
            ltd_tags = ['LongTermDebtNoncurrent', 'LongTermDebt', 'LongTermDebtAndCapitalLeaseObligations']
            long_term_debt = None
            for tag in ltd_tags:
                val = self._get_latest_value(facts, tag)
                if val is not None:
                    long_term_debt = val
                    break
                    
            # Total liabilities
            total_liabilities = self._get_latest_value(facts, 'Liabilities')
            
            # Compute default point
            # DP = STD + 0.5 * LTD. If unavailable, 0.5 * total_liabilities
            if short_term_debt is not None and long_term_debt is not None:
                default_point = short_term_debt + 0.5 * long_term_debt
            elif total_liabilities is not None:
                logger.warning(f"STD or LTD unavailable for {ticker}, using 0.5 * total_liabilities.")
                default_point = 0.5 * total_liabilities
                if short_term_debt is None: short_term_debt = 0.0
                if long_term_debt is None: long_term_debt = 0.0
            else:
                logger.error(f"Cannot compute default point for {ticker}.")
                raise ValueError(f"Insufficient debt data for {ticker}.")
                
            return {
                'short_term_debt': short_term_debt,
                'long_term_debt': long_term_debt,
                'total_liabilities': total_liabilities,
                'default_point': default_point
            }
        except Exception as e:
            logger.error(f"Error extracting debt data for {ticker}: {e}")
            raise

import pandas as pd
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

    def _get_historical_values(self, facts: dict, tag: str) -> pd.Series:
        """Helper to get historical values for a US-GAAP tag from 10-K and 10-Q as a time series."""
        try:
            concept = facts['facts']['us-gaap'].get(tag)
            if not concept:
                return pd.Series(dtype=float)
                
            units = concept.get('units', {})
            if 'USD' not in units:
                return pd.Series(dtype=float)
                
            data = units['USD']
            
            # Filter to 10-K and 10-Q forms
            valid_forms = [item for item in data if item.get('form') in ['10-K', '10-Q']]
            if not valid_forms:
                return pd.Series(dtype=float)
                
            # Create a dataframe
            df = pd.DataFrame(valid_forms)
            df['end'] = pd.to_datetime(df['end'])
            df = df.sort_values('end')
            # Drop duplicates by date, keeping the latest filed one if there are restatements
            df = df.drop_duplicates(subset=['end'], keep='last')
            
            series = pd.Series(df['val'].values, index=df['end'])
            return series
        except Exception as e:
            logger.debug(f"Error getting historical values for tag {tag}: {e}")
            return pd.Series(dtype=float)

    def extract_debt_data(self, ticker: str) -> dict:
        """Extract point-in-time historical debt data to compute the default point series."""
        try:
            import pandas as pd
            cik = self.get_cik_from_ticker(ticker)
            facts = self.fetch_company_facts(cik)
            
            # Short-term debt cascade
            std_tags = ['DebtCurrent', 'ShortTermBorrowings', 'LongTermDebtCurrent']
            std_series = pd.Series(dtype=float)
            for tag in std_tags:
                std_series = self._get_historical_values(facts, tag)
                if not std_series.empty:
                    break
                    
            # Long-term debt cascade
            ltd_tags = ['LongTermDebtNoncurrent', 'LongTermDebt', 'LongTermDebtAndCapitalLeaseObligations']
            ltd_series = pd.Series(dtype=float)
            for tag in ltd_tags:
                ltd_series = self._get_historical_values(facts, tag)
                if not ltd_series.empty:
                    break
                    
            # Total liabilities
            tl_series = self._get_historical_values(facts, 'Liabilities')
            
            # Align indices using an outer join
            df = pd.DataFrame({'std': std_series, 'ltd': ltd_series, 'tl': tl_series})
            df = df.ffill() # Forward fill missing values intra-quarter
            
            # Compute default point
            if not df['std'].isna().all() and not df['ltd'].isna().all():
                df['default_point'] = df['std'].fillna(0) + 0.5 * df['ltd'].fillna(0)
            elif not df['tl'].isna().all():
                logger.warning(f"STD or LTD unavailable for {ticker}, using 0.5 * total_liabilities.")
                df['default_point'] = 0.5 * df['tl']
            else:
                logger.error(f"Cannot compute default point for {ticker}.")
                raise ValueError(f"Insufficient debt data for {ticker}.")
                
            # Dropna for default point
            df = df.dropna(subset=['default_point'])
            
            return {
                'short_term_debt': float(df['std'].iloc[-1]) if not df.empty and not pd.isna(df['std'].iloc[-1]) else 0.0,
                'long_term_debt': float(df['ltd'].iloc[-1]) if not df.empty and not pd.isna(df['ltd'].iloc[-1]) else 0.0,
                'total_liabilities': float(df['tl'].iloc[-1]) if not df.empty and not pd.isna(df['tl'].iloc[-1]) else 0.0,
                'default_point': float(df['default_point'].iloc[-1]) if not df.empty else 0.0,
                'default_point_series': df['default_point']
            }
        except Exception as e:
            logger.error(f"Error extracting debt data for {ticker}: {e}")
            raise

    def fetch_financial_data(self, ticker: str, tags_dict: Dict[str, list]) -> dict:
        """Fetch multiple financial metrics using a dict of fallback tags."""
        try:
            cik = self.get_cik_from_ticker(ticker)
            facts = self.fetch_company_facts(cik)
            
            result = {}
            for metric, tags in tags_dict.items():
                value = None
                for tag in tags:
                    val = self._get_latest_value(facts, tag)
                    if val is not None:
                        value = val
                        break
                if value is None:
                    logger.warning(f"Could not find metric {metric} for {ticker} using tags {tags}")
                result[metric] = value
                
            return result
        except Exception as e:
            logger.error(f"Error fetching financial data for {ticker}: {e}")
            raise

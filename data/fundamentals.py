import yfinance as yf
import pandas as pd
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class UniversalFundamentals:
    """
    Fetches balance sheet and financial data for any global ticker using yfinance.
    Replaces the US-only SEC EDGAR dependency.
    """
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.yf_ticker = yf.Ticker(ticker)
        self.bs = self.yf_ticker.balance_sheet
        self.fin = self.yf_ticker.financials

    def _get_latest(self, df: pd.DataFrame, keys: list) -> Optional[float]:
        if df is None or df.empty:
            return None
        for key in keys:
            if key in df.index:
                # Get the most recent non-NaN value
                series = df.loc[key].dropna()
                if not series.empty:
                    return float(series.iloc[0])
        return None

    def extract_debt_data(self) -> Dict[str, float]:
        """Extract debt data to compute the default point."""
        std_keys = ['Short Long Term Debt', 'Current Debt', 'Current Liabilities']
        ltd_keys = ['Long Term Debt', 'Total Long Term Debt', 'Non Current Liabilities']
        tl_keys = ['Total Liabilities Net Minority Interest', 'Total Liabilities']

        short_term_debt = self._get_latest(self.bs, std_keys)
        long_term_debt = self._get_latest(self.bs, ltd_keys)
        total_liabilities = self._get_latest(self.bs, tl_keys)

        # Fallbacks
        if short_term_debt is None: short_term_debt = 0.0
        if long_term_debt is None and total_liabilities is not None:
            long_term_debt = total_liabilities - short_term_debt
        elif long_term_debt is None:
            long_term_debt = 0.0

        if short_term_debt > 0 and long_term_debt > 0:
            default_point = short_term_debt + 0.5 * long_term_debt
        elif total_liabilities is not None and total_liabilities > 0:
            default_point = 0.5 * total_liabilities
        else:
            default_point = 0.0
            logger.warning(f"Could not compute proper default point for {self.ticker}, returning 0.0")

        return {
            'short_term_debt': short_term_debt,
            'long_term_debt': long_term_debt,
            'total_liabilities': total_liabilities,
            'default_point': default_point
        }

    def fetch_financial_data(self) -> Dict[str, float]:
        """Fetch multiple financial metrics for Altman Z-Score."""
        assets_keys = ['Total Assets']
        current_assets_keys = ['Current Assets']
        current_liab_keys = ['Current Liabilities']
        retained_earnings_keys = ['Retained Earnings']
        ebit_keys = ['EBIT', 'Operating Income']
        revenue_keys = ['Total Revenue', 'Operating Revenue']

        total_assets = self._get_latest(self.bs, assets_keys) or 1.0 # avoid div/0
        current_assets = self._get_latest(self.bs, current_assets_keys) or 0.0
        current_liabilities = self._get_latest(self.bs, current_liab_keys) or 0.0
        retained_earnings = self._get_latest(self.bs, retained_earnings_keys) or 0.0
        ebit = self._get_latest(self.fin, ebit_keys) or 0.0
        revenue = self._get_latest(self.fin, revenue_keys) or 0.0
        total_liabilities = self._get_latest(self.bs, ['Total Liabilities Net Minority Interest', 'Total Liabilities']) or 0.0

        return {
            'total_assets': total_assets,
            'current_assets': current_assets,
            'current_liabilities': current_liabilities,
            'total_liabilities': total_liabilities,
            'retained_earnings': retained_earnings,
            'ebit': ebit,
            'revenue': revenue
        }

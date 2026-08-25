import pandas as pd
import re

with open('data/edgar.py', 'r') as f:
    content = f.read()

helper = """    def _get_historical_values(self, facts: dict, tag: str) -> pd.Series:
        \"\"\"Helper to get historical values for a US-GAAP tag from 10-K and 10-Q as a time series.\"\"\"
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
            return pd.Series(dtype=float)"""

old_extract = """    def extract_debt_data(self, ticker: str) -> dict:
        \"\"\"Extract debt data to compute the default point.\"\"\"
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
            raise"""

new_extract = """    def extract_debt_data(self, ticker: str) -> dict:
        \"\"\"Extract point-in-time historical debt data to compute the default point series.\"\"\"
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
            raise"""

content = content.replace("    def extract_debt_data", helper + "\n\n" + old_extract)
content = content.replace(old_extract, new_extract)
if "import pandas as pd" not in content:
    content = "import pandas as pd\n" + content

with open('data/edgar.py', 'w') as f:
    f.write(content)

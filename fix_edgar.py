import re

with open('data/edgar.py', 'r') as f:
    content = f.read()

# I will find everything from "def extract_debt_data" downwards up to "def fetch_financial_data" and replace it
# Wait, fetch_financial_data is right below it.
match = re.search(r'    def extract_debt_data.*?    def fetch_financial_data', content, re.DOTALL)
if match:
    bad_part = match.group(0)[:-len("    def fetch_financial_data")]
    
    good_part = """    def extract_debt_data(self, ticker: str) -> dict:
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
            raise\n\n"""
            
    content = content.replace(bad_part, good_part)
    with open('data/edgar.py', 'w') as f:
        f.write(content)
else:
    print("Could not find the block to replace!")

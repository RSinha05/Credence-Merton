import numpy as np
import pandas as pd
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

class ETFRiskEngine:
    """Calculates risk metrics specific to ETFs (VaR, MDD, Sharpe, Volatility)."""
    
    def __init__(self, ticker: str, risk_free_rate: float = 0.04):
        self.ticker = ticker
        self.rf_rate = risk_free_rate
        
    def fetch_data(self, period='2y') -> pd.DataFrame:
        logger.info(f"Fetching ETF historical data for {self.ticker}")
        df = yf.download(self.ticker, period=period, progress=False)
        if df.empty:
            raise ValueError(f"No data found for ETF {self.ticker}")
            
        # Handle multi-index columns from newer yfinance versions if needed
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(self.ticker, level=1, axis=1)
            
        df['return'] = df['Close'].pct_change()
        return df.dropna()
        
    def calculate_metrics(self, df: pd.DataFrame) -> dict:
        returns = df['return']
        
        # 1. Annualized Volatility
        daily_vol = returns.std()
        ann_vol = daily_vol * np.sqrt(252)
        
        # 2. Historical VaR (95%)
        var_95 = np.percentile(returns, 5)
        
        # 3. Maximum Drawdown
        cum_returns = (1 + returns).cumprod()
        rolling_max = cum_returns.cummax()
        drawdowns = (cum_returns - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
        # 4. Sharpe Ratio
        ann_return = returns.mean() * 252
        sharpe = (ann_return - self.rf_rate) / ann_vol if ann_vol > 0 else 0
        
        # 5. Determine Risk Tier based on VaR and MDD
        if max_drawdown < -0.30 or var_95 < -0.04:
            tier = "HIGH"
        elif max_drawdown < -0.15 or var_95 < -0.02:
            tier = "MEDIUM"
        else:
            tier = "LOW"
            
        return {
            "asset_type": "ETF",
            "annual_volatility": float(ann_vol),
            "var_95_daily": float(var_95),
            "max_drawdown": float(max_drawdown),
            "sharpe_ratio": float(sharpe),
            "risk_tier": tier
        }
        
    def run_assessment(self) -> dict:
        df = self.fetch_data()
        return self.calculate_metrics(df)

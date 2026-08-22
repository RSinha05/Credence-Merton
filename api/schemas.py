from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ModelType(str, Enum):
    MERTON = "MERTON"
    ALTMAN_Z = "ALTMAN_Z"
    ENSEMBLE = "ENSEMBLE"

class CorporateRiskRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    time_horizon: float = Field(1.0, description="Time horizon in years")
    include_altman: bool = Field(True, description="Whether to include Altman Z-Score calculation")
    include_time_series: bool = Field(False, description="Whether to include distance-to-default time series")

class PortfolioRiskRequest(BaseModel):
    tickers: List[str] = Field(..., description="List of stock ticker symbols")
    time_horizon: float = Field(1.0, description="Time horizon in years")

class MertonResult(BaseModel):
    sigma_V: float = Field(..., description="Asset volatility")
    DD_rn: float = Field(..., description="Risk-neutral distance to default")
    DD_rw: float = Field(..., description="Real-world distance to default")
    PD_rn: float = Field(..., description="Risk-neutral probability of default")
    PD_rw: float = Field(..., description="Real-world probability of default")
    V_current: float = Field(..., description="Current implied asset value")
    D: float = Field(..., description="Default point (Debt threshold)")
    iterations: float = Field(..., description="Number of iterations to converge")
    mu_rw: float = Field(..., description="Real-world asset drift")

class AltmanResult(BaseModel):
    z_score: Optional[float] = Field(None, description="Standard Altman Z-Score")
    z_zone: Optional[str] = Field(None, description="Distress Zone (Safe, Grey, Distress)")
    z_pp_score: Optional[float] = Field(None, description="Z''-Score for non-manufacturers")
    z_pp_zone: Optional[str] = Field(None, description="Z''-Score distress zone")
    x1: Optional[float] = Field(None, description="Working Capital / Total Assets")
    x2: Optional[float] = Field(None, description="Retained Earnings / Total Assets")
    x3: Optional[float] = Field(None, description="EBIT / Total Assets")
    x4: Optional[float] = Field(None, description="Market Value of Equity / Book Value of Total Liabilities")
    x5: Optional[float] = Field(None, description="Sales / Total Assets")

class EnsembleResult(BaseModel):
    ensemble_pd: float = Field(..., description="Aggregated probability of default")
    risk_tier: RiskTier = Field(..., description="Categorized risk tier")
    merton_pd: float = Field(..., description="Merton PD component")
    altman_pd_proxy: float = Field(..., description="Altman Z mapped PD proxy")
    models_agree: bool = Field(..., description="Whether both models indicate same general direction")
    confidence: float = Field(..., description="Confidence score of ensemble (0.0 to 1.0)")

class CorporateRiskResponse(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Company name")
    sp_rating: str = Field(..., description="Implied S&P Rating")
    computed_at: datetime = Field(..., description="Computation timestamp")
    merton: MertonResult = Field(..., description="Merton model results")
    altman: Optional[AltmanResult] = Field(None, description="Altman Z-Score results")
    ensemble: Optional[EnsembleResult] = Field(None, description="Ensemble model results")
    dd_timeseries: Optional[Dict[str, float]] = Field(None, description="Distance-to-default over time")
    pd_term_structure: Optional[Dict[float, float]] = Field(None, description="PD term structure")

class PortfolioRiskResponse(BaseModel):
    firms: List[CorporateRiskResponse] = Field(..., description="Individual firm risk analyses")
    portfolio_stats: dict = Field(..., description="Aggregated portfolio statistics")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API Version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    database_connected: bool = Field(..., description="Database connection status")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Specific error code identifier")

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

class Firm(Base):
    __tablename__ = "firms"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, index=True)
    name = Column(String(200))
    sp_rating = Column(String(10), nullable=True)
    moodys_rating = Column(String(10), nullable=True)
    sector = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, onupdate=utcnow)

    # Relationship: risk_results
    risk_results = relationship("RiskResult", back_populates="firm")

class RiskResult(Base):
    __tablename__ = "risk_results"

    id = Column(Integer, primary_key=True, index=True)
    firm_id = Column(Integer, ForeignKey("firms.id"))
    computed_at = Column(DateTime, default=utcnow)
    model_type = Column(String(50))  # 'merton', 'altman_z', 'ensemble'
    time_horizon = Column(Float)
    risk_free_rate = Column(Float)

    # Merton-specific fields (nullable for non-Merton results)
    sigma_v = Column(Float, nullable=True)
    dd_risk_neutral = Column(Float, nullable=True)
    dd_real_world = Column(Float, nullable=True)
    pd_risk_neutral = Column(Float, nullable=True)
    pd_real_world = Column(Float, nullable=True)
    asset_value = Column(Float, nullable=True)
    default_point = Column(Float, nullable=True)
    vk_iterations = Column(Integer, nullable=True)

    # Altman-specific fields (nullable for non-Altman results)
    z_score = Column(Float, nullable=True)
    z_zone = Column(String(20), nullable=True)
    z_pp_score = Column(Float, nullable=True)

    # Ensemble fields
    ensemble_pd = Column(Float, nullable=True)
    risk_tier = Column(String(20), nullable=True)
    models_agree = Column(Boolean, nullable=True)

    # Metadata
    raw_output = Column(JSON, nullable=True)  # full result dict for debugging
    
    # Relationship: firm
    firm = relationship("Firm", back_populates="risk_results")

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True)  # Celery task ID
    status = Column(String(20))  # 'pending', 'running', 'completed', 'failed'
    tickers = Column(Text)  # comma-separated tickers
    created_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

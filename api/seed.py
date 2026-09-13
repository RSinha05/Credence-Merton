import logging
from config import FIRM_PANEL
from db.database import SessionLocal, init_db
from db.models import Firm, RiskResult
import model.ensemble

logger = logging.getLogger(__name__)

def seed_database():
    init_db()
    db = SessionLocal()
    try:
        for firm_entry in FIRM_PANEL:
            firm = db.query(Firm).filter(Firm.ticker == firm_entry.ticker).first()
            if not firm:
                firm = Firm(
                    ticker=firm_entry.ticker,
                    name=firm_entry.name,
                    sp_rating=firm_entry.sp_rating,
                    moodys_rating=firm_entry.moodys_rating,
                    sector=getattr(firm_entry, 'sector', None),
                )
                db.add(firm)
                db.commit()
                db.refresh(firm)
            
            try:
                # The exact signature requested by the prompt
                res = model.ensemble.run_full_assessment(firm.ticker, T=1.0, r=0.04, include_altman=True)
                
                # Extract merton PD and DD
                merton_pd = res.get('merton', {}).get('PD_rn')
                merton_dd = res.get('merton', {}).get('DD_rn')
                
                rr = RiskResult(
                    firm_id=firm.id,
                    model_type='corporate_ews',
                    raw_output=res,
                    pd_risk_neutral=merton_pd,
                    dd_risk_neutral=merton_dd,
                    time_horizon=1.0,
                    risk_free_rate=0.04
                )
                db.add(rr)
                db.commit()
                logger.info(f"Seeded risk result for {firm.ticker}")
            except Exception as e:
                logger.error(f"Failed to run assessment for {firm.ticker}: {e}")
                db.rollback()
    finally:
        db.close()

def seed_if_empty():
    db = SessionLocal()
    try:
        count = db.query(RiskResult).count()
        if count < 5:
            logger.info(f"RiskResult has {count} rows. Seeding database...")
            seed_database()
        else:
            logger.info("Database already seeded.")
    finally:
        db.close()

import re

with open('api/routes/corporate.py', 'r') as f:
    content = f.read()

# Add RiskResult import if not there
if "RiskResult" not in content:
    content = content.replace("from db.database import get_db", "from db.database import get_db\nfrom db.models import Firm, RiskResult")

old_return = """        return CorporateRiskResponse("""

new_return = """        # Serialize for DB insertion
        import numpy as np
        import pandas as pd
        def serialize_for_db(obj):
            if isinstance(obj, pd.Series):
                return {str(k): v for k, v in obj.to_dict().items()}
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, dict):
                return {k: serialize_for_db(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [serialize_for_db(i) for i in obj]
            return obj
        
        full_res = {'merton': merton_res, 'altman': altman_res, 'ensemble': ensemble_res}
        clean_res = serialize_for_db(full_res)
        
        firm = db.query(Firm).filter(Firm.ticker == ticker).first()
        if not firm:
            firm = Firm(ticker=ticker, name=f"{ticker} Corp", sp_rating="NR", moodys_rating="NR", sector="Unknown")
            db.add(firm)
            db.commit()
            db.refresh(firm)
            
        risk_record = RiskResult(firm_id=firm.id, model_type='corporate_ews', raw_output=clean_res)
        db.add(risk_record)
        db.commit()

        return CorporateRiskResponse("""

content = content.replace(old_return, new_return)

with open('api/routes/corporate.py', 'w') as f:
    f.write(content)

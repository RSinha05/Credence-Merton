import re

with open('api/routes/multi_asset.py', 'r') as f:
    content = f.read()

# Imports
old_imports = """from data.fundamentals import fetch_financials, get_market_data"""
new_imports = """from data.fundamentals import fetch_financials, get_market_data
from api.routes.nlp import get_nlp_sentiment
from db.database import get_db"""
content = content.replace(old_imports, new_imports)

# Equity logic
old_equity = """        # Run Merton model
        merton_res = run_single_firm(
            equity_series=hist,
            D=default_point,
            r=0.04,
            T=1.0
        )"""

new_equity = """        # Run NLP Sentiment
        sentiment_score = 0.0
        try:
            # We need a DB session. We can just yield from get_db
            db_session = next(get_db())
            nlp_res = get_nlp_sentiment(ticker, db_session)
            sentiment_score = nlp_res.get("sentiment_score", 0.0)
        except Exception as e:
            logger.warning(f"Failed to fetch NLP sentiment for {ticker}: {e}")

        # Run Merton model
        merton_res = run_single_firm(
            equity_series=hist,
            D=default_point,
            r=0.04,
            T=1.0,
            sentiment_score=sentiment_score
        )
        
        # Inject sentiment into the response metrics
        merton_res["sentiment_score"] = sentiment_score
"""
content = content.replace(old_equity, new_equity)

with open('api/routes/multi_asset.py', 'w') as f:
    f.write(content)

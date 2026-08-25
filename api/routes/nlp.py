from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from db.database import get_db
from db.models import SentimentAnalysis, Firm
from data.sec_scraper import fetch_latest_8k_text
from model.nlp_sentiment import analyze_sentiment

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{ticker}")
def get_nlp_sentiment(ticker: str, db: Session = Depends(get_db)):
    """
    Fetches the latest SEC 8-K filing, runs FinBERT on it,
    and returns a net sentiment score. Uses DB caching.
    """
    ticker = ticker.upper()
    
    # 1. Check cache
    cached = db.query(SentimentAnalysis).filter(SentimentAnalysis.ticker == ticker).order_by(SentimentAnalysis.created_at.desc()).first()
    
    # If cached recently (e.g., today), return it
    if cached:
        # Simple caching: return the latest
        return {
            "ticker": ticker,
            "document_type": cached.document_type,
            "sentiment_score": cached.sentiment_score,
            "cached": True
        }
        
    # 2. Scrape EDGAR
    logger.info(f"Fetching 8-K for {ticker}")
    text = fetch_latest_8k_text(ticker)
    
    if not text:
        # Fallback or error
        return {
            "ticker": ticker,
            "document_type": "None",
            "sentiment_score": 0.0,
            "cached": False,
            "message": "No recent 8-K found or scraping failed."
        }
        
    # 3. Analyze Sentiment
    logger.info(f"Running FinBERT for {ticker}")
    score = analyze_sentiment(text)
    
    # 4. Save to DB
    sa = SentimentAnalysis(
        ticker=ticker,
        document_type="8-K",
        filing_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        raw_text_snippet=text[:1000], # save snippet
        sentiment_score=score
    )
    db.add(sa)
    db.commit()
    db.refresh(sa)
    
    return {
        "ticker": ticker,
        "document_type": "8-K",
        "sentiment_score": score,
        "cached": False
    }

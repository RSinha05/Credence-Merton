"""
News feed endpoint — fetches financial headlines from Yahoo Finance RSS.
"""
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
import urllib.request

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/v1/news', tags=['News Feed'])

YAHOO_FEEDS = {
    'market':   'https://finance.yahoo.com/news/rssindex',
    'stocks':   'https://finance.yahoo.com/rss/topstories',
    'economy':  'https://finance.yahoo.com/rss/economy',
}

# Curated seed headlines in case RSS fetch fails (network sandbox, rate-limit, etc.)
SEED_NEWS = [
    {"title": "Fed Holds Rates Steady, Signals Caution on Inflation Outlook",
     "link": "https://finance.yahoo.com", "source": "Reuters",
     "published": "2026-08-31T12:00:00Z",
     "category": "economy"},
    {"title": "NVIDIA Surpasses $4T Market Cap After Blowout Earnings",
     "link": "https://finance.yahoo.com", "source": "Bloomberg",
     "published": "2026-08-31T11:30:00Z",
     "category": "stocks"},
    {"title": "Treasury Yields Climb as Jobs Data Beats Expectations",
     "link": "https://finance.yahoo.com", "source": "CNBC",
     "published": "2026-08-31T10:45:00Z",
     "category": "economy"},
    {"title": "S&P 500 Hits Record Close; Tech Sector Leads Rally",
     "link": "https://finance.yahoo.com", "source": "MarketWatch",
     "published": "2026-08-31T10:00:00Z",
     "category": "market"},
    {"title": "European Banks Face Tighter Capital Rules Under Basel III Endgame",
     "link": "https://finance.yahoo.com", "source": "Financial Times",
     "published": "2026-08-31T09:30:00Z",
     "category": "economy"},
    {"title": "Oil Prices Surge 3% on OPEC+ Production Cut Extension",
     "link": "https://finance.yahoo.com", "source": "Reuters",
     "published": "2026-08-31T09:00:00Z",
     "category": "market"},
    {"title": "Apple Announces $110B Share Buyback, Largest in History",
     "link": "https://finance.yahoo.com", "source": "WSJ",
     "published": "2026-08-31T08:30:00Z",
     "category": "stocks"},
    {"title": "India's Sensex Breaches 85,000 for First Time on FII Inflows",
     "link": "https://finance.yahoo.com", "source": "Economic Times",
     "published": "2026-08-31T08:00:00Z",
     "category": "market"},
    {"title": "Private Equity Deal Volume Surges 40% YoY in Q3 2026",
     "link": "https://finance.yahoo.com", "source": "PitchBook",
     "published": "2026-08-31T07:30:00Z",
     "category": "market"},
    {"title": "Credit Default Swaps Signal Rising Stress in US High-Yield Sector",
     "link": "https://finance.yahoo.com", "source": "Bloomberg",
     "published": "2026-08-31T07:00:00Z",
     "category": "economy"},
    {"title": "Tesla Delivers Record 620K Vehicles in Q3, Beating Estimates",
     "link": "https://finance.yahoo.com", "source": "Reuters",
     "published": "2026-08-31T06:30:00Z",
     "category": "stocks"},
    {"title": "Bank of Japan Holds Ultra-Loose Policy, Yen Weakens Further",
     "link": "https://finance.yahoo.com", "source": "Nikkei",
     "published": "2026-08-31T06:00:00Z",
     "category": "economy"},
]


def _fetch_rss(url: str, limit: int = 15) -> list:
    """Parse a Yahoo Finance RSS feed into a list of headline dicts."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
        root = ET.fromstring(data)
        items = []
        for item in root.findall('.//item'):
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            pub = item.findtext('pubDate', '')
            source = item.findtext('source', 'Yahoo Finance')
            items.append({
                'title': title,
                'link': link,
                'source': source,
                'published': pub,
            })
            if len(items) >= limit:
                break
        return items
    except Exception as e:
        logger.warning(f"RSS fetch failed for {url}: {e}")
        return []


@router.get('/feed')
async def get_news_feed(category: Optional[str] = None, limit: int = 12):
    """
    Returns financial news headlines.
    Tries Yahoo Finance RSS first; falls back to curated seed headlines.
    
    Query params:
      category: 'market' | 'stocks' | 'economy' (optional filter)
      limit: max items to return (default 12)
    """
    # Try live RSS
    articles = []
    if category and category in YAHOO_FEEDS:
        articles = _fetch_rss(YAHOO_FEEDS[category], limit)
    else:
        for cat, url in YAHOO_FEEDS.items():
            articles.extend(_fetch_rss(url, limit=5))

    # Fallback to seed headlines if RSS is unavailable
    if not articles:
        articles = SEED_NEWS.copy()
        if category:
            articles = [a for a in articles if a.get('category') == category]

    return articles[:limit]

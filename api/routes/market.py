from fastapi import APIRouter, HTTPException, Depends
import yfinance as yf
from config import FIRM_PANEL

router = APIRouter(prefix="/api/v1/market", tags=["Market"])

@router.get("/live/{ticker}")
def get_live_market_data(ticker: str):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if not info or ("currentPrice" not in info and "regularMarketPrice" not in info):
            raise ValueError("No price data found")
            
        return {
            "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
            "change_pct": info.get("regularMarketChangePercent", 0.0),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "market_cap": info.get("marketCap"),
            "volume": info.get("volume"),
            "beta": info.get("beta"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield")
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found: {str(e)}")

@router.get("/movers")
def get_movers():
    results = []
    for firm in FIRM_PANEL:
        try:
            t = yf.Ticker(firm.ticker)
            info = t.info
            cp = info.get("currentPrice", info.get("regularMarketPrice"))
            prev = info.get("previousClose", info.get("regularMarketPreviousClose"))
            
            if cp and prev:
                change_pct = ((cp - prev) / prev) * 100.0
            else:
                change_pct = info.get("regularMarketChangePercent", 0.0)
                
            results.append({
                "ticker": firm.ticker,
                "current_price": cp,
                "change_pct": change_pct
            })
        except Exception:
            continue
            
    # Sort by change_pct
    results.sort(key=lambda x: x["change_pct"] or 0)
    top_losers = results[:5]
    top_gainers = sorted(results, key=lambda x: x["change_pct"] or 0, reverse=True)[:5]
    
    return {
        "top_gainers": top_gainers,
        "top_losers": top_losers
    }

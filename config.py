"""
config.py — Global configuration for the Merton/KMV Distance-to-Default model.

Contains:
- Firm panel definition (tickers, ratings, ordinals)
- Model parameters (T, lookback, convergence)
- SEC EDGAR settings
- Output paths
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# Model Parameters
# ──────────────────────────────────────────────────────────────────────────────

T_HORIZON: float = 1.0                # Default time horizon (years)
LOOKBACK_DAYS: int = 252              # Trading days for historical vol
VK_MAX_ITER: int = 50                 # Max Vasicek-Kealhofer iterations
VK_TOL: float = 1e-6                 # Convergence tolerance for sigma_V
TRADING_DAYS_PER_YEAR: int = 252      # Annualization factor

# PD term structure horizons (years)
PD_TERM_HORIZONS: List[float] = [0.5, 1.0, 2.0, 3.0, 5.0]

# ──────────────────────────────────────────────────────────────────────────────
# SEC EDGAR Settings
# ──────────────────────────────────────────────────────────────────────────────

SEC_USER_AGENT: str = "CredenceMertonX research@credencemertonx.com"
SEC_RATE_LIMIT_DELAY: float = 0.12    # Seconds between requests (~8 req/sec)

# ──────────────────────────────────────────────────────────────────────────────
# Rating Ordinal Mapping (1 = AAA ... 21 = D)
# ──────────────────────────────────────────────────────────────────────────────

RATING_TO_ORDINAL: Dict[str, int] = {
    "AAA": 1,
    "AA+": 2,  "AA": 3,   "AA-": 4,
    "A+": 5,   "A": 6,    "A-": 7,
    "BBB+": 8, "BBB": 9,  "BBB-": 10,
    "BB+": 11, "BB": 12,  "BB-": 13,
    "B+": 14,  "B": 15,   "B-": 16,
    "CCC+": 17, "CCC": 18, "CCC-": 19,
    "CC": 20,
    "D": 21,
}

# ──────────────────────────────────────────────────────────────────────────────
# Firm Panel — Spanning Investment Grade to High Yield
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class FirmEntry:
    """A single firm in the analysis panel."""
    ticker: str
    name: str
    sp_rating: str
    moodys_rating: str
    ordinal: int  # Numeric ordinal from RATING_TO_ORDINAL


# Curated panel of ~15 firms across credit quality tiers.
# Ratings sourced from public financial data as of mid-2025.
FIRM_PANEL: List[FirmEntry] = [
    # ── Investment Grade (IG) ─────────────────────────────────────────────
    FirmEntry("MSFT",  "Microsoft Corp",           "AAA",  "Aaa",   1),
    FirmEntry("JNJ",   "Johnson & Johnson",        "AAA",  "Aaa",   1),
    FirmEntry("AAPL",  "Apple Inc",                "AA+",  "Aaa",   2),
    FirmEntry("GOOG",  "Alphabet Inc",             "AA+",  "Aa2",   2),
    FirmEntry("PG",    "Procter & Gamble",         "AA-",  "Aa3",   4),

    # ── Mid-Grade (BBB territory) ─────────────────────────────────────────
    FirmEntry("GM",    "General Motors",           "BBB",  "Baa2",  9),
    FirmEntry("F",     "Ford Motor Co",            "BBB-", "Baa3",  10),
    FirmEntry("DAL",   "Delta Air Lines",          "BBB-", "Baa3",  10),
    FirmEntry("LUV",   "Southwest Airlines",       "BBB",  "Baa1",  9),
    FirmEntry("BA",    "Boeing Co",                "BBB-", "Baa2",  10),

    # ── High Yield / Speculative ──────────────────────────────────────────
    FirmEntry("AAL",   "American Airlines",        "B+",   "B1",    14),
    FirmEntry("DISH",  "DISH Network",             "CCC+", "Caa2",  17),
    FirmEntry("RIG",   "Transocean Ltd",           "CCC+", "Caa1",  17),
    FirmEntry("CLF",   "Cleveland-Cliffs",         "B+",   "B2",    14),
    FirmEntry("COTY",  "Coty Inc",                 "B+",   "B1",    14),
]


def get_tickers() -> List[str]:
    """Return list of all panel tickers."""
    return [f.ticker for f in FIRM_PANEL]


def get_firm_by_ticker(ticker: str) -> FirmEntry:
    """Look up a firm entry by ticker symbol."""
    for f in FIRM_PANEL:
        if f.ticker.upper() == ticker.upper():
            return f
    raise ValueError(f"Ticker '{ticker}' not found in firm panel.")


# ──────────────────────────────────────────────────────────────────────────────
# Output Paths
# ──────────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Altman Z-Score Thresholds (Manufacturing / Public Firms)
# ──────────────────────────────────────────────────────────────────────────────

ALTMAN_Z_SAFE: float = 2.99        # Z > 2.99 → Safe zone
ALTMAN_Z_GREY_UPPER: float = 2.99  # 1.81 < Z < 2.99 → Grey zone
ALTMAN_Z_GREY_LOWER: float = 1.81
ALTMAN_Z_DISTRESS: float = 1.81    # Z < 1.81 → Distress zone

# Altman Z'' (non-manufacturing / emerging markets) thresholds
ALTMAN_ZPP_SAFE: float = 2.60
ALTMAN_ZPP_DISTRESS: float = 1.10

# US-GAAP tags for Z-Score accounting ratios (SEC EDGAR)
ALTMAN_EDGAR_TAGS: Dict[str, List[str]] = {
    "total_assets": ["Assets"],
    "current_assets": ["AssetsCurrent"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "total_liabilities": ["Liabilities"],
    "retained_earnings": ["RetainedEarningsAccumulatedDeficit"],
    "ebit": [
        "OperatingIncomeLoss",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    ],
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
}


# ──────────────────────────────────────────────────────────────────────────────
# API / Backend Settings
# ──────────────────────────────────────────────────────────────────────────────

API_TITLE: str = "Credence-MertonX Credit Risk Engine"
API_VERSION: str = "1.0.0"
API_DESCRIPTION: str = (
    "Market-implied credit risk analytics: Distance-to-Default, "
    "Altman Z-Score, and ensemble bankruptcy prediction."
)

# Database — defaults to SQLite for development, PostgreSQL for production
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(PROJECT_ROOT, 'credence.db')}"
)

# Celery / Redis
CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")


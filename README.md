# Credence-MertonX: Merton/KMV Distance-to-Default Credit Risk Model

A production-grade implementation of the **Merton (1974) structural credit model** — treating equity as a call option on firm assets — to compute market-implied default probabilities, validated against agency credit ratings.

This is the theoretical backbone of **Moody's KMV**, one of the most widely used commercial credit-risk products in banking.

---

## Theory

### Core Model — Equity as a Call Option

Merton (1974): equity holders have a call option on firm assets with strike = face value of debt.

$$E = V \cdot N(d_1) - D \cdot e^{-rT} \cdot N(d_2)$$

$$d_1 = \frac{\ln(V/D) + (r + \frac{1}{2}\sigma_V^2)T}{\sigma_V\sqrt{T}}, \quad d_2 = d_1 - \sigma_V\sqrt{T}$$

Where:
- **E** = equity market cap (observed)
- **V** = total asset value (unknown)
- **D** = default point (KMV: STD + 0.5 × LTD)
- **σ_V** = asset volatility (unknown)
- **r** = risk-free rate
- **T** = time horizon (1 year)

### Two Equations, Two Unknowns

The second equation comes from Itô's lemma:

$$\sigma_E \cdot E = N(d_1) \cdot \sigma_V \cdot V$$

### Vasicek-Kealhofer Iterative Solver (What KMV Actually Does)

Rather than naively solving both equations simultaneously (unstable with noisy single-day σ_E), we use the iterative approach:

1. **Seed**: σ_V⁽⁰⁾ = σ_E · E / (E + D)
2. **For each day**: invert the equity equation to solve for V_t given current σ_V
3. **Recompute**: σ_V from log-returns of the inferred V_t series
4. **Repeat** until σ_V converges (~5–10 iterations)

### Distance-to-Default & Probability of Default

$$DD = \frac{\ln(V/D) + (\mu - \frac{1}{2}\sigma_V^2)T}{\sigma_V\sqrt{T}}$$

$$PD = N(-DD)$$

- Use μ = r for **risk-neutral PD**
- Use historical asset drift for **real-world PD**

> **Caveat**: N(-DD) assumes normally distributed asset returns, which understates real-world default rates (fat tails). Moody's KMV maps DD → empirical EDF using a proprietary default database. We use N(-DD) as the best available proxy.

### KMV Default Point

Firms don't default at total liabilities — they default around short-term obligations:

$$D = \text{STD} + 0.5 \times \text{LTD}$$

---

## Project Structure

```
Credence-MertonX/
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── config.py                     # Global settings, firm panel, constants
├── main.py                       # Entry point — runs full pipeline
│
├── data/                         # Data acquisition layer
│   ├── equity.py                 # Yahoo Finance: market cap, equity vol
│   ├── edgar.py                  # SEC EDGAR: balance sheet debt
│   ├── risk_free.py              # FRED/Yahoo: risk-free rate
│   └── ratings.py                # Credit rating panel
│
├── model/                        # Quantitative modeling layer
│   ├── merton.py                 # VK iteration, DD, PD computation
│   └── validation.py             # Spearman rank correlation
│
├── visualization/                # Charting layer
│   └── plots.py                  # 4 publication-quality charts
│
└── output/                       # Generated charts & CSV results
    ├── dd_time_series.png
    ├── pd_vs_rating.png
    ├── asset_vs_barrier.png
    ├── pd_term_structure.png
    └── results_summary.csv
```

---

## Installation

```bash
# Clone or navigate to project directory
cd Credence-MertonX

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Optional: FRED API Key

For the most reliable risk-free rate data, set a FRED API key:

```bash
export FRED_API_KEY="your_api_key_here"
```

Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html

The model works without one (falls back to FRED public CSV or Yahoo Finance).

---

## Usage

```bash
python main.py
```

The pipeline will:
1. Fetch the current risk-free rate
2. For each firm in the panel (~15 firms spanning AAA to CCC):
   - Pull equity market cap and compute historical volatility
   - Pull balance sheet debt from SEC EDGAR
   - Run Vasicek-Kealhofer iteration to solve for asset value & volatility
   - Compute Distance-to-Default and implied probability of default
3. Validate by computing Spearman rank correlation vs. agency ratings
4. Generate all visualizations
5. Export results to `output/results_summary.csv`

---

## Firm Panel

| Tier | Tickers | Rating Range |
|------|---------|-------------|
| **Investment Grade** | MSFT, JNJ, AAPL, GOOG, PG | AAA to AA- |
| **Mid-Grade** | GM, F, DAL, LUV, BA | BBB to BBB- |
| **High Yield** | AAL, DISH, RIG, CLF, COTY | B+ to CCC+ |

---

## Output Visualizations

| Chart | Description |
|-------|-------------|
| **DD Time Series** | Distance-to-Default over trailing 252 days for representative firms |
| **PD vs. Rating Scatter** | Implied PD plotted against rating ordinal — Spearman ρ annotated |
| **Asset Value vs. Barrier** | Inferred V_t series vs. horizontal default point D |
| **PD Term Structure** | PD at T = 0.5, 1, 2, 3, 5 years |

---

## Data Sources

| Data | Source | Cost |
|------|--------|------|
| Equity market cap & vol | Yahoo Finance (`yfinance`) | Free |
| Balance sheet debt (STD, LTD) | SEC EDGAR XBRL API | Free |
| Risk-free rate | FRED (Federal Reserve) | Free |
| Credit ratings | Curated panel (public knowledge) | Free |

---

## Validation Metric

**Spearman rank correlation** between model-implied PD and agency rating ordinals. Expected: ρ > 0.5 with p < 0.05, confirming that the model correctly rank-orders credit risk.

---

## How This Is Used in Industry

- **Moody's Analytics KMV**: This exact Merton framework is the core of the KMV Expected Default Frequency (EDF) product, used by virtually every major bank's credit risk department.
- **Bank credit risk teams**: Forward-looking, market-implied PDs that move faster than rating-agency downgrades.
- **Hedge funds**: Credit long/short strategies use DD as a signal — declining DD preceded most corporate defaults by 6-12 months.
- **Regulators**: Basel II/III internal-ratings-based approach allows banks to use models like this for regulatory capital calculation.

---

## Core Quantitative Concepts

- Merton (1974) structural credit model
- Black-Scholes option pricing (equity as a call)
- Vasicek-Kealhofer iterative solver
- Distance-to-Default (DD)
- Market-implied probability of default (PD)
- Risk-neutral vs. real-world default measures

---

## Python Libraries

- `numpy` / `scipy` — numerical computation, optimization, statistics
- `pandas` — data manipulation
- `yfinance` — equity market data
- `requests` — SEC EDGAR API calls
- `matplotlib` / `seaborn` — visualization

---

## License

MIT License. For educational and research purposes.

# Model Card: Altman Z-Score & Z''-Score

## 1. Description
An empirical bankruptcy prediction model based on accounting ratios. The engine supports both the original Z-Score (manufacturing) and Z''-Score (non-manufacturing/emerging markets).

## 2. Assumptions
- Financial statements accurately reflect the firm's economic reality.
- The original coefficients (fitted in 1968) remain robust across modern economic environments.

## 3. Known Limitations
- **Accounting Lag**: Relies on quarterly EDGAR 10-K/10-Q filings, which are inherently backward-looking compared to daily market prices.
- **Sector Bias**: The original Z-Score highly penalizes non-asset-heavy tech companies.

## 4. Validation Method
- **EDGAR Fallback Tagging**: Validated to smoothly fall back through various US-GAAP tags (e.g. `DebtCurrent` -> `ShortTermBorrowings`) if primary tags are missing.

## 5. Metadata
- **Last Validated**: August 2026
- **Owner**: Credence-MertonX Fundamental Team

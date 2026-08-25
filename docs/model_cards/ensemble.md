# Model Card: Ensemble Credit Risk Engine

## 1. Description
Combines the structural Merton/KMV model (market-implied, fast-moving) and Altman Z-Score (accounting-based, stable) to produce a unified default probability.

## 2. Assumptions
- Market prices ($Merton$) and accounting data ($Altman$) contain orthogonal, additive information.
- The weighting scheme (70% Merton / 30% Altman) optimally captures distress without overreacting to short-term volatility.

## 3. Known Limitations
- If SEC data is missing or out-of-date, the ensemble defaults to 100% Merton, exposing the score to pure market volatility without fundamental anchoring.

## 4. Validation Method
- **Key-Match Tracing**: Verified end-to-end integration mapping between `merton_results` (returning `PD_rn`) and the ensemble risk computer.

## 5. Metadata
- **Last Validated**: August 2026
- **Owner**: Credence-MertonX Quant Team

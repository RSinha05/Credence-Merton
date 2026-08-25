# Model Card: Merton/KMV Structural Credit Model

## 1. Description
The Merton/KMV model computes Distance-to-Default (DD) and Probability of Default (PD) by treating a firm's equity as a European call option on its assets. 
Our implementation uses a vectorized Vasicek-Kealhofer (VK) iterative solver.

## 2. Assumptions
- Firm asset value follows a Geometric Brownian Motion (GBM).
- Debt is a single zero-coupon bond maturing at $T$.
- Equity is a European call option on the firm's assets, with strike price $D$.

## 3. Known Limitations
- **Fat-tail Understatement**: The standard structural model assumes log-normal returns. This understates empirical default probabilities (especially for low/moderate DDs) due to fat tails in real-world asset returns. We mitigate this using `DDCalibrator`.
- **Synthetic Calibration Data**: The EDF mapping currently relies on synthetic monotonic data simulating Moody's KMV logic. 
- **Not for Private Firms**: Requires observable, traded equity prices (daily).

## 4. Validation Method
- **Closed-Form Round-Trip**: We verify that feeding back implied asset values and volatility perfectly recovers observed equity.
- **Root-Bracketing Verification**: Verified via $N(d_1)$ boundary checks inside Newton-Raphson.

## 5. Metadata
- **Last Validated**: August 2026
- **Owner**: Credence-MertonX Quant Team

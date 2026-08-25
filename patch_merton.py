import re

with open('model/merton.py', 'r') as f:
    content = f.read()

# Replace run_single_firm definition
old_def = """def run_single_firm(
    equity_series: pd.Series,
    D: float,
    r: float,
    T: float = 1.0,
    max_iter: int = 50,
    tol: float = 1e-6
) -> dict:"""

new_def = """def run_single_firm(
    equity_series: pd.Series,
    D: float,
    r: float,
    T: float = 1.0,
    max_iter: int = 50,
    tol: float = 1e-6,
    sentiment_score: float = None
) -> dict:"""

content = content.replace(old_def, new_def)

old_body = """    # Real-world drift mu (annualized mean of log returns)
    log_returns_V = np.log(asset_series / asset_series.shift(1)).dropna()
    mu_rw = log_returns_V.mean() * 252

    # DD
    dd_rn = compute_distance_to_default(V_current, D, sigma_V, r, T)"""

new_body = """    # NLP Sentiment Adjustment
    if sentiment_score is not None:
        # Scale volatility based on sentiment (-1.0 to +1.0)
        # E.g., highly negative (-1) -> +20% volatility
        # highly positive (+1) -> -10% volatility
        # Linear interpolation
        vol_modifier = -0.15 * sentiment_score + 0.05
        sigma_V = sigma_V * (1.0 + vol_modifier)
        logger.info(f"Applied NLP Sentiment {sentiment_score:.2f} -> Adjusted sigma_V to {sigma_V:.4f}")

    # Real-world drift mu (annualized mean of log returns)
    log_returns_V = np.log(asset_series / asset_series.shift(1)).dropna()
    mu_rw = log_returns_V.mean() * 252

    # DD
    dd_rn = compute_distance_to_default(V_current, D, sigma_V, r, T)"""

content = content.replace(old_body, new_body)

with open('model/merton.py', 'w') as f:
    f.write(content)

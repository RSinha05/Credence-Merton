import re

with open('model/merton.py', 'r') as f:
    content = f.read()

# Make solve_merton_vk accept D as float or Series
old_solve_sig = """def solve_merton_vk(
    equity_series: pd.Series,
    D: float,
    r: float,
    T: float = 1.0,"""

new_solve_sig = """def solve_merton_vk(
    equity_series: pd.Series,
    D: float | pd.Series,
    r: float,
    T: float = 1.0,"""
content = content.replace(old_solve_sig, new_solve_sig)

# Inside solve_merton_vk, align D
old_init = """    # Initialize V array for vectorized Newton-Raphson
    E = equity_series.values
    V = E + D"""

new_init = """    # Align D with equity_series if D is a pandas Series
    if isinstance(D, pd.Series):
        D_aligned = D.reindex(equity_series.index, method='ffill').bfill().values
    else:
        D_aligned = float(D)

    # Initialize V array for vectorized Newton-Raphson
    E = equity_series.values
    V = E + D_aligned
    D = D_aligned  # Override D with the aligned array or float for the loop"""
content = content.replace(old_init, new_init)

# Same for run_single_firm
old_run_sig = """def run_single_firm(
    equity_series: pd.Series,
    D: float,
    r: float,"""

new_run_sig = """def run_single_firm(
    equity_series: pd.Series,
    D: float | pd.Series,
    r: float,"""
content = content.replace(old_run_sig, new_run_sig)

# In run_single_firm, use the last value of D for scalar computations like compute_pd_term_structure
old_d_val = """    V_current = asset_series.iloc[-1]"""
new_d_val = """    V_current = asset_series.iloc[-1]
    D_current = D.iloc[-1] if isinstance(D, pd.Series) else D"""
content = content.replace(old_d_val, new_d_val)

content = content.replace("compute_distance_to_default(V_current, D, sigma_V, r, T)", "compute_distance_to_default(V_current, D_current, sigma_V, r, T)")
content = content.replace("compute_distance_to_default(V_current, D, sigma_V, mu_rw, T)", "compute_distance_to_default(V_current, D_current, sigma_V, mu_rw, T)")
content = content.replace("compute_dd_time_series(asset_series, D, sigma_V, mu_rw, T)", "compute_dd_time_series(asset_series, D, sigma_V, mu_rw, T)")
content = content.replace("compute_pd_term_structure(V_current, D, sigma_V, mu_rw)", "compute_pd_term_structure(V_current, D_current, sigma_V, mu_rw)")

# Update compute_dd_time_series to handle D as a series
old_ts = """def compute_dd_time_series(
    asset_series: pd.Series,
    D: float,
    sigma_V: float,
    mu: float,
    T: float = 1.0
) -> pd.Series:
    \"\"\"
    Computes Distance-to-Default (DD) for each date in the asset series.
    \"\"\"
    return asset_series.apply(lambda v: compute_distance_to_default(v, D, sigma_V, mu, T))"""

new_ts = """def compute_dd_time_series(
    asset_series: pd.Series,
    D: float | pd.Series,
    sigma_V: float,
    mu: float,
    T: float = 1.0
) -> pd.Series:
    \"\"\"
    Computes Distance-to-Default (DD) for each date in the asset series.
    \"\"\"
    if isinstance(D, pd.Series):
        D_aligned = D.reindex(asset_series.index, method='ffill').bfill()
        return pd.Series([
            compute_distance_to_default(v, d, sigma_V, mu, T) 
            for v, d in zip(asset_series, D_aligned)
        ], index=asset_series.index)
    else:
        return asset_series.apply(lambda v: compute_distance_to_default(v, D, sigma_V, mu, T))"""
content = content.replace(old_ts, new_ts)

# Finally replace D in the return statement
content = content.replace('"D": D', '"D": float(D_current)')

with open('model/merton.py', 'w') as f:
    f.write(content)

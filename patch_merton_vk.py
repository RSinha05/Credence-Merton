import re

with open('model/merton.py', 'r') as f:
    content = f.read()

# Replace the inner loop
old_loop = """    for i in range(max_iter):
        # a. For each day t, solve for V_t
        for t, E_t in equity_series.items():
            lower_bound = max(E_t * 0.5, 1.0)
            upper_bound = E_t + 3 * D
            
            try:
                # Bracket check
                val_lower = _merton_equity_equation(lower_bound, E_t, D, r, T, sigma_V)
                val_upper = _merton_equity_equation(upper_bound, E_t, D, r, T, sigma_V)
                
                if val_lower * val_upper > 0:
                    # Broaden bracket
                    lower_bound = max(E_t * 0.1, 0.1)
                    upper_bound = E_t + 10 * D
                    val_lower = _merton_equity_equation(lower_bound, E_t, D, r, T, sigma_V)
                    val_upper = _merton_equity_equation(upper_bound, E_t, D, r, T, sigma_V)
                    
                    if val_lower * val_upper > 0:
                        logger.warning(f"Failed to bracket root for date {t}. Using previous day's V_t if available.")
                        if len(asset_series.dropna()) > 0:
                            asset_series.loc[t] = asset_series.dropna().iloc[-1]
                        else:
                            asset_series.loc[t] = E_t + D
                        continue

                v_opt = brentq(_merton_equity_equation, lower_bound, upper_bound, args=(E_t, D, r, T, sigma_V))
                asset_series.loc[t] = v_opt

            except Exception as e:
                logger.warning(f"Optimization failed on date {t}: {e}")
                if len(asset_series.dropna()) > 0:
                    asset_series.loc[t] = asset_series.dropna().iloc[-1]
                else:
                    asset_series.loc[t] = E_t + D
        
        # b. Compute log returns of the V_t series
        log_returns_V = np.log(asset_series / asset_series.shift(1)).dropna()
        
        # c. Recompute sigma_V_new
        sigma_V_new = log_returns_V.std(ddof=1) * np.sqrt(252)
        
        # d. If |sigma_V_new - sigma_V| < tol: converged
        if abs(sigma_V_new - sigma_V) < tol:
            return asset_series, sigma_V_new, sigma_V, i + 1
            
        # e. update
        sigma_V_prev = sigma_V
        sigma_V = sigma_V_new
        
    logger.warning("Vasicek-Kealhofer Iterative Solver did not converge within the maximum number of iterations.")
    return asset_series, sigma_V, sigma_V_prev, max_iter"""

new_loop = """    # Initialize V array for vectorized Newton-Raphson
    E = equity_series.values
    V = E + D
    
    for i in range(max_iter):
        sigma_V_prev = sigma_V
        
        # a. Solve for V_t using vectorized Newton-Raphson
        for _ in range(10): # inner Newton iterations
            d1 = (np.log(V / D) + (r + 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T))
            d2 = d1 - sigma_V * np.sqrt(T)
            
            BS_Call = V * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)
            error = BS_Call - E
            
            # Derivative of call with respect to V is N(d1)
            dV = error / norm.cdf(d1)
            V = V - dV
            
            if np.max(np.abs(error)) < 1e-4:
                break
                
        # Floor V to E to prevent impossible states
        V = np.maximum(V, E + 1e-4)
        asset_series[:] = V
        
        # b. Compute log returns of the V_t series
        log_returns_V = np.log(asset_series / asset_series.shift(1)).dropna()
        
        # c. Recompute sigma_V_new
        sigma_V_new = log_returns_V.std(ddof=1) * np.sqrt(252)
        
        # d. Converged?
        if abs(sigma_V_new - sigma_V) < tol:
            return asset_series, sigma_V_new, sigma_V, i + 1
            
        sigma_V = sigma_V_new
        
    logger.warning("Vasicek-Kealhofer Iterative Solver did not converge within the maximum number of iterations.")
    return asset_series, sigma_V, sigma_V_prev, max_iter"""

if old_loop in content:
    content = content.replace(old_loop, new_loop)
else:
    print("Could not find old loop block.")
    
with open('model/merton.py', 'w') as f:
    f.write(content)

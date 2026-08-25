import re

with open('model/merton.py', 'r') as f:
    content = f.read()

old_return = """    return {
        "asset_series": asset_series,
        "sigma_V": sigma_V,
        "DD_rn": dd_rn,
        "DD_rw": dd_rw,
        "PD_rn": pd_rn,
        "PD_rw": pd_rw,
        "PD_calibrated": float(pd_calibrated) if pd_calibrated is not None else None,
        "dd_timeseries": dd_timeseries,
        "pd_term_structure": pd_term_structure,
        "iterations": n_iter,
        "mu_rw": mu_rw,
        "V_current": V_current
    }"""

new_return = """    return {
        "asset_series": asset_series,
        "sigma_V": sigma_V,
        "DD_rn": dd_rn,
        "DD_rw": dd_rw,
        "PD_rn": pd_rn,
        "PD_rw": pd_rw,
        "PD_calibrated": float(pd_calibrated) if pd_calibrated is not None else None,
        "dd_timeseries": dd_timeseries,
        "pd_term_structure": pd_term_structure,
        "iterations": n_iter,
        "mu_rw": mu_rw,
        "V_current": V_current,
        "D": D
    }"""

content = content.replace(old_return, new_return)

with open('model/merton.py', 'w') as f:
    f.write(content)

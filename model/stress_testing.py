import logging
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, Any
from model.merton import run_single_firm

logger = logging.getLogger(__name__)

STRESS_SCENARIOS = {
    'ccar_baseline': {'name': 'CCAR Baseline', 'r_shock': 0.0, 'vol_multiplier': 1.0, 'dp_multiplier': 1.0, 'equity_shock': 0.0},
    'ccar_adverse': {'name': 'CCAR Adverse', 'r_shock': -0.01, 'vol_multiplier': 1.3, 'dp_multiplier': 1.1, 'equity_shock': -0.15},
    'ccar_severely_adverse': {'name': 'CCAR Severely Adverse', 'r_shock': -0.02, 'vol_multiplier': 1.6, 'dp_multiplier': 1.2, 'equity_shock': -0.30},
    'eba_adverse': {'name': 'EBA Adverse', 'r_shock': -0.015, 'vol_multiplier': 1.5, 'dp_multiplier': 1.15, 'equity_shock': -0.25},
    'pandemic': {'name': 'Pandemic Shock', 'r_shock': -0.025, 'vol_multiplier': 2.0, 'dp_multiplier': 1.0, 'equity_shock': -0.35},
    'rate_hike': {'name': 'Rapid Rate Hike', 'r_shock': 0.03, 'vol_multiplier': 1.4, 'dp_multiplier': 1.05, 'equity_shock': -0.10}
}

def apply_stress_scenario(equity_series: pd.Series, D: float, r: float, scenario: dict) -> Tuple[pd.Series, float, float]:
    """
    Apply stress scenario shocks to inputs.
    
    Args:
        equity_series (pd.Series): Historical equity values.
        D (float): Default point / Debt value.
        r (float): Risk-free rate.
        scenario (dict): Stress scenario parameters.
        
    Returns:
        Tuple[pd.Series, float, float]: (E_stressed, D_stressed, r_stressed)
    """
    equity_shock = scenario.get('equity_shock', 0.0)
    dp_multiplier = scenario.get('dp_multiplier', 1.0)
    r_shock = scenario.get('r_shock', 0.0)
    
    E_stressed = equity_series * (1.0 + equity_shock)
    D_stressed = D * dp_multiplier
    r_stressed = max(r + r_shock, 0.001)
    
    return E_stressed, D_stressed, r_stressed

def run_stress_test(equity_series: pd.Series, D: float, r: float, T: float = 1.0, scenarios: Optional[Dict[str, Dict]] = None) -> Dict[str, Any]:
    """
    Run stress tests across multiple scenarios.
    
    Args:
        equity_series (pd.Series): Historical equity values.
        D (float): Debt value.
        r (float): Risk-free rate.
        T (float): Time to maturity.
        scenarios (dict, optional): Custom scenarios to run. Defaults to STRESS_SCENARIOS.
        
    Returns:
        dict: Stress test results including base_case, scenario_results, and worst_case.
    """
    if scenarios is None:
        scenarios = STRESS_SCENARIOS
        
    logger.info("Running base case...")
    base_res = run_single_firm(equity_series, D, r, T)
    
    scenario_results = {}
    worst_pd = -1.0
    worst_case = None
    
    for sc_name, sc_params in scenarios.items():
        logger.info(f"Running scenario: {sc_name}")
        E_str, D_str, r_str = apply_stress_scenario(equity_series, D, r, sc_params)
        
        try:
            res = run_single_firm(E_str, D_str, r_str, T)
            
            scenario_results[sc_name] = {
                'DD_rn': float(res['DD_rn']),
                'PD_rn': float(res['PD_rn']),
                'sigma_V': float(res['sigma_V']),
                'V_current': float(res['V_current']),
                'D_stressed': float(D_str),
                'r_stressed': float(r_str)
            }
            
            if float(res['PD_rn']) > worst_pd:
                worst_pd = float(res['PD_rn'])
                worst_case = sc_name
                
        except Exception as e:
            logger.error(f"Error running scenario {sc_name}: {e}")
            
    return {
        'scenario_results': scenario_results,
        'base_case': {
            'DD_rn': float(base_res['DD_rn']),
            'PD_rn': float(base_res['PD_rn']),
            'sigma_V': float(base_res['sigma_V']),
            'V_current': float(base_res['V_current']),
            'D': float(D),
            'r': float(r)
        },
        'worst_case': worst_case
    }

def stress_test_summary(stress_results: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert stress test results to a summary DataFrame.
    
    Args:
        stress_results (dict): Output from run_stress_test.
        
    Returns:
        pd.DataFrame: Summary of scenario results.
    """
    base = stress_results['base_case']
    scenario_results = stress_results['scenario_results']
    
    rows = []
    for sc_name, res in scenario_results.items():
        rows.append({
            'scenario': sc_name,
            'DD_rn': res['DD_rn'],
            'PD_rn': res['PD_rn'],
            'sigma_V': res['sigma_V'],
            'delta_DD': res['DD_rn'] - base['DD_rn'],
            'delta_PD': res['PD_rn'] - base['PD_rn']
        })
        
    return pd.DataFrame(rows)

def run_panel_stress_test(panel_data: Dict[str, Tuple[pd.Series, float, float]], scenarios: Optional[Dict[str, Dict]] = None) -> Dict[str, Any]:
    """
    Run stress tests for a panel of firms.
    
    Args:
        panel_data: Dict mapping ticker to (equity_series, D, r)
        scenarios: Optional custom scenarios
        
    Returns:
        dict: Contains individual firm results and 'panel_summary' DataFrame
    """
    firm_results = {}
    summary_rows = []
    
    for ticker, (eq, d, r) in panel_data.items():
        logger.info(f"Running panel stress test for {ticker}")
        try:
            res = run_stress_test(eq, d, r, T=1.0, scenarios=scenarios)
            firm_results[ticker] = res
            
            worst_scenario = res['worst_case']
            worst_pd = res['scenario_results'][worst_scenario]['PD_rn'] if worst_scenario else None
            
            summary_rows.append({
                'ticker': ticker,
                'base_PD': res['base_case']['PD_rn'],
                'worst_PD': worst_pd,
                'worst_scenario': worst_scenario
            })
        except Exception as e:
            logger.error(f"Failed stress test for {ticker}: {e}")
            
    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
    else:
        summary_df = pd.DataFrame(columns=['ticker', 'base_PD', 'worst_PD', 'worst_scenario'])
        
    return {
        'firm_results': firm_results,
        'panel_summary': summary_df
    }

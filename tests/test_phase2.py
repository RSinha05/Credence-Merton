"""Tests for Phase 2 bank-grade modules."""
import pytest
import numpy as np
import pandas as pd


class TestRegulatoryCapital:
    def test_capital_requirement_positive(self):
        from model.regulatory_capital import compute_capital_requirement
        res = compute_capital_requirement(pd_val=0.02, lgd=0.45)
        assert res['K'] > 0
        assert 0 < res['RWA_density'] < 5.0
        assert 0 < res['rho'] < 0.24

    def test_capital_monotonic_in_pd(self):
        from model.regulatory_capital import compute_capital_requirement
        k_low = compute_capital_requirement(pd_val=0.005, lgd=0.45)['K']
        k_high = compute_capital_requirement(pd_val=0.05, lgd=0.45)['K']
        assert k_high > k_low, "Capital requirement should increase with PD"

    def test_pd_floor(self):
        from model.regulatory_capital import compute_asset_correlation
        rho = compute_asset_correlation(pd_val=0.00001)
        assert rho > 0


class TestTTCPIT:
    def test_dd_to_rating_bucket(self):
        from model.ttc_pit import dd_to_rating_bucket
        assert dd_to_rating_bucket(6.0) == 'AAA'
        assert dd_to_rating_bucket(3.5) == 'A'
        assert dd_to_rating_bucket(1.2) == 'B'
        assert dd_to_rating_bucket(-0.5) == 'D'

    def test_ttc_vs_pit(self):
        from model.ttc_pit import compute_ttc_pit_comparison
        mock_merton = {'DD_rn': 3.5, 'DD_rw': 3.2, 'PD_rn': 0.001, 'PD_rw': 0.002}
        res = compute_ttc_pit_comparison(mock_merton)
        assert 'ttc' in res
        assert 'pit' in res
        assert 'ratio' in res


class TestCECL:
    def test_lifetime_pd(self):
        from model.cecl import compute_lifetime_pd
        pd_ts = {0.5: 0.001, 1.0: 0.005, 2.0: 0.02, 3.0: 0.04, 5.0: 0.10}
        lp = compute_lifetime_pd(pd_ts)
        assert 0 < lp <= 1.0

    def test_scenario_weighting(self):
        from model.cecl import compute_cecl_expected_loss
        mock_merton = {
            'pd_term_structure': {0.5: 0.001, 1.0: 0.005, 2.0: 0.015, 3.0: 0.03, 5.0: 0.07},
            'PD_rn': 0.005
        }
        res = compute_cecl_expected_loss(mock_merton, lgd=0.45)
        assert res['weighted_lifetime_pd'] > 0
        assert res['cecl_expected_loss'] > 0
        baseline_lpd = res['scenario_results']['baseline']['lifetime_pd']
        adverse_lpd = res['scenario_results']['adverse']['lifetime_pd']
        assert adverse_lpd >= baseline_lpd


class TestPortfolioRisk:
    def test_analytical_var(self):
        from model.portfolio_risk import vasicek_analytical_var
        var = vasicek_analytical_var(pd_val=0.02, lgd=0.45, rho=0.15)
        assert 0 < var < 1.0

    def test_var_monotonic_in_correlation(self):
        from model.portfolio_risk import vasicek_analytical_var
        var_low = vasicek_analytical_var(pd_val=0.02, lgd=0.45, rho=0.05)
        var_high = vasicek_analytical_var(pd_val=0.02, lgd=0.45, rho=0.25)
        assert var_high > var_low, "VaR should increase with correlation"


class TestMigration:
    def test_dd_to_rating(self):
        from model.migration import dd_to_rating
        assert dd_to_rating(6.0) == 'A++'
        assert dd_to_rating(2.5) == 'B++'
        assert dd_to_rating(-1.0) == 'D'

    def test_transition_matrix_rows_sum_to_one(self):
        from model.migration import compute_transition_matrix
        ratings = pd.Series(['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D',
                             'AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D'])
        matrix = compute_transition_matrix(ratings)
        for idx, row in matrix.iterrows():
            row_sum = row.sum()
            if row_sum > 0:
                assert abs(row_sum - 1.0) < 1e-6, f"Row {idx} sums to {row_sum}"


class TestStressTesting:
    def test_scenarios_defined(self):
        from model.stress_testing import STRESS_SCENARIOS
        assert 'ccar_baseline' in STRESS_SCENARIOS
        assert 'ccar_severely_adverse' in STRESS_SCENARIOS
        assert 'pandemic' in STRESS_SCENARIOS

    def test_apply_stress_scenario(self):
        from model.stress_testing import apply_stress_scenario
        dates = pd.date_range('2024-01-01', periods=50, freq='B')
        equity = pd.Series(np.random.uniform(100, 200, 50), index=dates)
        scenario = {'equity_shock': -0.30, 'dp_multiplier': 1.2, 'r_shock': -0.02,
                    'vol_multiplier': 1.5, 'name': 'test'}
        E_s, D_s, r_s = apply_stress_scenario(equity, D=50.0, r=0.05, scenario=scenario)
        assert (E_s < equity).all(), "Stressed equity should be lower"
        assert D_s > 50.0, "Stressed default point should be higher"
        assert r_s < 0.05, "Stressed rate should be lower"

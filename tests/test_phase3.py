"""Tests for Phase 3 PE-grade modules."""
import pytest
import numpy as np
import pandas as pd


class TestPrivateComps:
    def test_find_comps_by_sector(self):
        from data.private_comps import PrivateCompany, find_comparable_companies
        co = PrivateCompany(name='TestCo', sector='Tech', geography='US',
                            ebitda=100, total_debt=300, equity_book_value=200, revenue=500)
        comps = find_comparable_companies(co, n_comps=5)
        assert len(comps) > 0
        assert all(c.sector == 'Tech' for c in comps)

    def test_peer_multiples(self):
        from data.private_comps import PrivateCompany, find_comparable_companies, compute_peer_multiples
        co = PrivateCompany(name='TestCo', sector='Healthcare', geography='US',
                            ebitda=200, total_debt=400, equity_book_value=300, revenue=1000)
        comps = find_comparable_companies(co)
        if comps:
            mults = compute_peer_multiples(comps)
            assert mults['median_ev_ebitda'] > 0
            assert mults['n_comps'] > 0


class TestPrivateFirm:
    def test_proxy_asset_value(self):
        from model.private_firm import proxy_asset_value
        V = proxy_asset_value(ebitda=100, peer_ev_ebitda=12.0)
        assert V == 1200.0

    def test_hamada_unlever(self):
        from model.private_firm import hamada_unlever_vol
        sigma_a = hamada_unlever_vol(equity_vol=0.30, leverage_de=1.0)
        assert 0 < sigma_a < 0.30, "Unlevered vol should be lower than equity vol"

    def test_run_private_firm(self):
        from data.private_comps import PrivateCompany
        from model.private_firm import run_private_firm_model
        co = PrivateCompany(name='TestCo', sector='Industrials', geography='US',
                            ebitda=200, total_debt=600, equity_book_value=300, revenue=1200)
        res = run_private_firm_model(co)
        assert res['methodology'] == 'Moodys Private Firm Model'
        assert 'DD' in res
        assert 'PD' in res


class TestLBOSchedule:
    def test_sample_lbo(self):
        from data.lbo_schedule import create_sample_lbo, build_debt_schedule
        deal = create_sample_lbo()
        schedule = build_debt_schedule(deal)
        assert 'total_debt' in schedule.columns
        assert schedule['total_debt'].iloc[0] > schedule['total_debt'].iloc[-1], \
            "Total debt should decrease over time due to amortization"

    def test_maturity_wall(self):
        from data.lbo_schedule import create_sample_lbo, compute_maturity_wall
        deal = create_sample_lbo()
        mw = compute_maturity_wall(deal)
        assert 'refinancing_risk' in mw
        assert mw['refinancing_risk'] in ['LOW', 'MEDIUM', 'HIGH']

    def test_default_point_series(self):
        from data.lbo_schedule import create_sample_lbo, get_default_point_series
        deal = create_sample_lbo()
        dp = get_default_point_series(deal)
        assert isinstance(dp, pd.Series)
        assert len(dp) > 0


class TestCalibrationPrivate:
    def test_private_calibrator_higher_edf(self):
        from model.calibration_private import get_private_calibrator
        from model.calibration import DDCalibrator
        private_cal = get_private_calibrator()
        public_cal = DDCalibrator()
        public_cal.fit_synthetic()

        dd_test = 2.0
        private_edf = private_cal.predict(dd_test)
        public_edf = public_cal.predict(dd_test)
        assert private_edf > public_edf, \
            "Private EDF should be higher than public EDF at the same DD"


class TestLBOEarlyWarning:
    def test_detect_deterioration(self):
        from model.lbo_early_warning import detect_deterioration
        # Create a deteriorating DD trajectory
        dates = pd.date_range('2024-01-01', periods=12, freq='QS')
        dd_values = [4.0, 3.8, 3.5, 3.2, 2.8, 2.5, 2.1, 1.8, 1.5, 1.2, 1.0, 0.8]
        dd_series = pd.Series(dd_values, index=dates)
        result = detect_deterioration(dd_series)
        assert result['trend'] == 'deteriorating'
        assert result['below_distress'] is True

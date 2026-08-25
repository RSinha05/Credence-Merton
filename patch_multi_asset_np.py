with open('api/routes/multi_asset.py', 'r') as f:
    content = f.read()

old_insert = """            risk_record = RiskResult(
                firm_id=firm.id,
                model_type='merton',
                time_horizon=1.0,
                risk_free_rate=rf_rate,
                sigma_v=res.get('sigma_V'),
                dd_risk_neutral=res.get('DD_rn'),
                pd_risk_neutral=res.get('PD_rn'),
                asset_value=res.get('V_current'),
                default_point=debt_data['default_point'],
                raw_output=clean_res
            )"""

new_insert = """            risk_record = RiskResult(
                firm_id=firm.id,
                model_type='merton',
                time_horizon=1.0,
                risk_free_rate=float(rf_rate) if rf_rate is not None else None,
                sigma_v=float(res.get('sigma_V')) if res.get('sigma_V') is not None else None,
                dd_risk_neutral=float(res.get('DD_rn')) if res.get('DD_rn') is not None else None,
                pd_risk_neutral=float(res.get('PD_rn')) if res.get('PD_rn') is not None else None,
                asset_value=float(res.get('V_current')) if res.get('V_current') is not None else None,
                default_point=float(debt_data['default_point']) if debt_data.get('default_point') is not None else None,
                raw_output=clean_res
            )"""

content = content.replace(old_insert, new_insert)

with open('api/routes/multi_asset.py', 'w') as f:
    f.write(content)

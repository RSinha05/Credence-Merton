with open('api/routes/multi_asset.py', 'r') as f:
    content = f.read()

import re

# We will just strip ALL complex types before inserting to the database. We don't need to save the entire time series array to PostgreSQL, just the top-level metrics.
old_block = """            # Persist to Supabase / DB
            risk_record = RiskResult(
                firm_id=firm.id,
                model_type='merton',
                time_horizon=1.0,
                risk_free_rate=rf_rate,
                sigma_v=res.get('sigma_V'),
                dd_risk_neutral=res.get('DD_rn'),
                pd_risk_neutral=res.get('PD_rn'),
                asset_value=res.get('V_current'),
                default_point=debt_data['default_point'],
                raw_output={"asset_class": "EQUITY", **res}
            )"""

new_block = """            # Strip complex objects for DB persistence to prevent JSON serialization errors
            clean_res = {k: v for k, v in res.items() if isinstance(v, (int, float, str, bool, type(None)))}
            clean_res['asset_class'] = 'EQUITY'

            # Persist to Supabase / DB
            risk_record = RiskResult(
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

content = content.replace(old_block, new_block)

with open('api/routes/multi_asset.py', 'w') as f:
    f.write(content)

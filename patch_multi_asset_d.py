import re

with open('api/routes/multi_asset.py', 'r') as f:
    content = f.read()

content = content.replace("D=debt_data['default_point']", "D=debt_data.get('default_point_series', debt_data['default_point'])")
content = content.replace("default_point=d_point", "default_point=float(debt_data['default_point']) if debt_data.get('default_point') is not None else None")

with open('api/routes/multi_asset.py', 'w') as f:
    f.write(content)

import re
with open('workers/tasks.py', 'r') as f:
    content = f.read()

content = content.replace("D=debt_data['default_point']", "D=debt_data.get('default_point_series', debt_data['default_point'])")

with open('workers/tasks.py', 'w') as f:
    f.write(content)

with open('api/routes/corporate.py', 'r') as f:
    corp_content = f.read()

corp_content = corp_content.replace("D=debt_data['default_point']", "D=debt_data.get('default_point_series', debt_data['default_point'])")

with open('api/routes/corporate.py', 'w') as f:
    f.write(corp_content)

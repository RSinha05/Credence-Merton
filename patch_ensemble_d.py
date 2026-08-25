import re
with open('model/ensemble.py', 'r') as f:
    content = f.read()

content = content.replace("D: float", "D: float | pd.Series")

with open('model/ensemble.py', 'w') as f:
    f.write(content)

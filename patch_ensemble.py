with open('model/ensemble.py', 'r') as f:
    content = f.read()

# Fix key-mismatch for PD
content = content.replace("merton_pd = merton_results.get('pd', 0.0)", "merton_pd = merton_results.get('PD_rn', 0.0)")

with open('model/ensemble.py', 'w') as f:
    f.write(content)

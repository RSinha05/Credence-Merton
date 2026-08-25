import re

with open('model/altman_z.py', 'r') as f:
    content = f.read()

old_code = """    try:
        raw_data = client.fetch_financial_data(ticker, config.ALTMAN_EDGAR_TAGS)
    except AttributeError:
        # Fallback pseudo-method
        raw_data = client.get_financials(ticker, config.ALTMAN_EDGAR_TAGS)"""

new_code = """    # Fetch financials using configured tags. Will explicitly raise exceptions on failure.
    raw_data = client.fetch_financial_data(ticker, config.ALTMAN_EDGAR_TAGS)"""

content = content.replace(old_code, new_code)

with open('model/altman_z.py', 'w') as f:
    f.write(content)

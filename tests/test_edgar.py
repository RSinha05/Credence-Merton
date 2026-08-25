import pytest
import pandas as pd
from data.edgar import SECEdgarClient
from unittest.mock import patch, MagicMock

@patch('data.edgar.SECEdgarClient.fetch_company_facts')
@patch('data.edgar.SECEdgarClient.get_cik_from_ticker')
def test_edgar_fallback_tags(mock_get_cik, mock_fetch):
    mock_get_cik.return_value = '0000320193'
    
    # Mock response missing some primary tags
    mock_fetch.return_value = {
        'facts': {
            'us-gaap': {
                'ShortTermBorrowings': {
                    'units': {
                        'USD': [{'end': '2023-12-31', 'val': 1000, 'form': '10-K'}]
                    }
                },
                'LongTermDebt': {
                    'units': {
                        'USD': [{'end': '2023-12-31', 'val': 5000, 'form': '10-K'}]
                    }
                }
            }
        }
    }
    
    client = SECEdgarClient()
    debt_data = client.extract_debt_data('AAPL')
    
    assert debt_data['short_term_debt'] == 1000.0
    assert debt_data['long_term_debt'] == 5000.0
    assert debt_data['default_point'] == 1000.0 + 0.5 * 5000.0

import requests
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# SEC requires a user agent with a company name and email
HEADERS = {
    "User-Agent": "Aurelis Intelligence risk-engine@aurelis.com"
}

def get_cik_from_ticker(ticker: str) -> str:
    """Fetch the CIK for a given ticker."""
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    
    for entry in data.values():
        if entry['ticker'] == ticker.upper():
            # CIKs in SEC URLs are typically 10 digits padded with zeros
            return str(entry['cik_str']).zfill(10)
            
    raise ValueError(f"CIK not found for ticker {ticker}")

def fetch_latest_8k_text(ticker: str) -> str:
    """Fetches the text of the latest 8-K filing for a given ticker."""
    try:
        cik = get_cik_from_ticker(ticker)
    except Exception as e:
        logger.error(f"Error fetching CIK for {ticker}: {e}")
        return ""
        
    # Get the company's submissions
    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(submissions_url, headers=HEADERS)
    if response.status_code != 200:
        logger.error(f"Error fetching submissions for CIK {cik}")
        return ""
        
    data = response.json()
    recent = data.get("filings", {}).get("recent", {})
    
    if not recent:
        return ""
        
    # Find the latest 8-K
    forms = recent.get("form", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_documents = recent.get("primaryDocument", [])
    
    latest_8k_index = -1
    for i, form in enumerate(forms):
        if form == "8-K":
            latest_8k_index = i
            break
            
    if latest_8k_index == -1:
        logger.info(f"No recent 8-K found for {ticker}")
        return ""
        
    acc_num = accession_numbers[latest_8k_index].replace("-", "")
    primary_doc = primary_documents[latest_8k_index]
    
    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_num}/{primary_doc}"
    logger.info(f"Fetching 8-K from {doc_url}")
    
    doc_response = requests.get(doc_url, headers=HEADERS)
    if doc_response.status_code != 200:
        return ""
        
    # Parse HTML
    soup = BeautifulSoup(doc_response.content, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    
    # We only want the first few thousand characters to feed into FinBERT, 
    # as 8-Ks can be massive.
    return text[:5000]

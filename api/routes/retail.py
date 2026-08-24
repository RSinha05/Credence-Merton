import logging
import pandas as pd
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict

from api.schemas import RetailPortfolioRequest, RetailPortfolioResponse, RetailLoanResponse

try:
    from model.retail_credit import RetailRiskEngine
    from data.synthetic_mortgage import MortgageDataGenerator
except ImportError:
    pass

router = APIRouter(prefix='/api/v1/risk/retail', tags=['Retail Mortgage Risk'])
logger = logging.getLogger(__name__)

# Global instances (in production, you'd load models from disk or a bucket)
_RETAIL_ENGINE = None

def get_engine():
    global _RETAIL_ENGINE
    if _RETAIL_ENGINE is None:
        _RETAIL_ENGINE = RetailRiskEngine()
        # For demo purposes, if models aren't loaded, we generate data and train immediately
        logger.info("Initializing Retail Risk Engine and training on synthetic data...")
        generator = MortgageDataGenerator()
        df = generator.generate_loan_tape(n_loans=10000)
        
        # Features and targets
        features = df[['fico_score', 'ltv', 'dti', 'loan_amount', 'interest_rate']]
        pd_labels = df['default_flag']
        
        # Train PD
        _RETAIL_ENGINE.fit_pd_model(features, pd_labels)
        
        # Train LGD (only on defaulted loans for realism)
        defaulted = df[df['default_flag'] == 1]
        if len(defaulted) > 0:
            lgd_features = defaulted[['fico_score', 'ltv', 'dti', 'loan_amount', 'interest_rate']]
            lgd_targets = defaulted['recovery_rate']
            _RETAIL_ENGINE.fit_lgd_model(lgd_features, lgd_targets)
            
        logger.info("Retail Risk Engine initialized successfully.")
    return _RETAIL_ENGINE


@router.post('/portfolio', response_model=RetailPortfolioResponse)
async def analyze_retail_portfolio(request: RetailPortfolioRequest):
    """
    Analyze risk (Expected Loss) for a portfolio of retail mortgages.
    """
    logger.info(f"Analyzing retail portfolio with {len(request.loans)} loans")
    
    try:
        engine = get_engine()
        
        # Convert request to DataFrame
        loan_dicts = [loan.dict() for loan in request.loans]
        df = pd.DataFrame(loan_dicts)
        
        features = df[['fico_score', 'ltv', 'dti', 'loan_amount', 'interest_rate']]
        months_seasoned = df['months_seasoned']
        term_months = df['term_months']
        
        # Predict Expected Loss components
        results_df = engine.predict_expected_loss(features, months_seasoned, term_months)
        
        # Package response
        loan_results = []
        total_ead = 0.0
        total_el = 0.0
        
        for idx, row in results_df.iterrows():
            loan_id = loan_dicts[idx]['loan_id']
            ead = row['EAD']
            el = row['expected_loss']
            
            total_ead += ead
            total_el += el
            
            loan_results.append(
                RetailLoanResponse(
                    loan_id=loan_id,
                    pd=row['PD'],
                    lgd=row['LGD'],
                    ead=ead,
                    expected_loss=el
                )
            )
            
        return RetailPortfolioResponse(
            portfolio_total_ead=total_ead,
            portfolio_expected_loss=total_el,
            loan_results=loan_results
        )
        
    except Exception as e:
        logger.exception("Error analyzing retail portfolio")
        raise HTTPException(status_code=500, detail=str(e))

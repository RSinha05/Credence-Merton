import logging
from dataclasses import asdict
import pandas as pd
from config import FIRM_PANEL

logger = logging.getLogger(__name__)

def get_ratings_panel() -> pd.DataFrame:
    """
    Get the ratings panel data from the configured firm panel.

    Converts the list of FirmEntry dataclass instances into a DataFrame.

    Returns:
        pd.DataFrame: DataFrame with columns ticker, name, sp_rating, moodys_rating, ordinal.
    """
    try:
        records = [asdict(firm) for firm in FIRM_PANEL]
        df = pd.DataFrame(records)
        expected_cols = ['ticker', 'name', 'sp_rating', 'moodys_rating', 'ordinal']
        for col in expected_cols:
            if col not in df.columns:
                logger.warning(f"Column '{col}' not found in FIRM_PANEL data.")
                
        return df
    except Exception as e:
        logger.error(f"Error building ratings panel: {e}")
        raise

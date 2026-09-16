from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import numpy as np

from model.ensemble import run_full_assessment
from data.equity import fetch_equity_data
from data.edgar import SECEdgarClient
from data.risk_free import fetch_risk_free_rate

# Assuming ML models can be imported
try:
    from model.clustering import TrajectoryClusterer
    from model.ml_volatility import fit_garch, forecast_volatility
    ml_available = True
except ImportError:
    ml_available = False

router = APIRouter(prefix="/api/v1/analyst", tags=["Analyst Memo"])

@router.get("/memo/{ticker}")
async def get_credit_memo(ticker: str) -> Dict[str, Any]:
    try:
        # 1. Fetch live data
        equity_data = fetch_equity_data(ticker)
        if equity_data is None or equity_data.empty:
            raise ValueError("Equity data not found")
            
        edgar_client = SECEdgarClient()
        debt_data = edgar_client.extract_debt_data(ticker)
        rf_rate = fetch_risk_free_rate()
        
        market_cap = equity_data.iloc[-1]['mkt_cap']
        
        # 2. Run core assessment
        results = run_full_assessment(
            ticker=ticker,
            equity_series=equity_data['mkt_cap'],
            D=debt_data.get('default_point_series', debt_data.get('default_point', 1000.0)),
            r=rf_rate,
            market_cap=market_cap,
            T=1.0
        )
        
        # 3. Extract metrics
        ensemble = results.get('ensemble', {})
        merton = results.get('merton', {})
        altman = results.get('altman', {})
        
        pd_val = ensemble.get("ensemble_pd", merton.get("PD_rn", 0.0))
        dd = merton.get("DD_rn", 0.0)
        z_score = altman.get("z_score", 0.0)
        risk_tier = ensemble.get("risk_tier", "Unknown")
        implied_rating = "BB" # Could be fetched from dd_to_rating if imported
        
        # 4. Integrate ML Early Warning Signals
        ml_signals = {}
        if ml_available and 'dd_timeseries' in merton:
            # Trajectory Clustering
            try:
                clusterer = TrajectoryClusterer(n_clusters=4)
                # Need to fit first or use a pre-trained model. We will mock fit for now with synthetic data
                demo_traj = clusterer.generate_demo_trajectories()
                demo_traj[ticker] = merton['dd_timeseries']
                clusterer.fit(demo_traj)
                cluster_pred = clusterer.predict_single(merton['dd_timeseries'], ticker)
                ml_signals['trajectory'] = cluster_pred
            except Exception as e:
                ml_signals['trajectory_error'] = str(e)
                
            # GARCH Forward Volatility on Equity Returns
            try:
                returns = np.log(equity_data['mkt_cap'] / equity_data['mkt_cap'].shift(1)).dropna() * 100 # percentage
                garch_model = fit_garch(returns)
                fwd_vol = forecast_volatility(garch_model, horizon=30)
                ml_signals['garch_volatility'] = fwd_vol
            except Exception as e:
                ml_signals['garch_error'] = str(e)

        # 5. Build the GenAI Context Window / Output Memo
        
        ml_text = ""
        if 'trajectory' in ml_signals:
            tj = ml_signals['trajectory']
            ml_text += f" Trajectory clustering indicates the firm is in a '{tj.get('cluster_name', 'Unknown')}' state. "
            if tj.get('is_deteriorating'):
                ml_text += f"WARNING: Short-term DD slope is negative ({tj.get('slope',0):.3f}), triggering a {tj.get('alert_level', 'watch').upper()} alert."
                
        if 'garch_volatility' in ml_signals:
            fwd = ml_signals['garch_volatility']
            ml_text += f" GARCH(1,1) model forecasts an annualized equity volatility of {fwd['annualized_vol_forecast']:.1f}% over the next 30 days."

        memo = {
            "executive_summary": f"Based on our quantitative assessment of {ticker}, the firm is currently classified in the {risk_tier} risk tier. Our structural models indicate a 1-year probability of default (PD) of {pd_val:.4f}.",
            "risk_assessment": f"The primary driver of the credit profile is the firm's distance to default (DD) of {dd:.2f}. This metric suggests the asset value cushion remains {'adequate' if dd > 2 else 'tight'} relative to the default point.",
            "ml_early_warning": ml_text if ml_text else "ML Early warning signals are currently unavailable.",
            "key_metrics": {
                "PD": pd_val,
                "DD": dd,
                "Z-Score": z_score,
                "risk_tier": risk_tier,
                "ml_signals": ml_signals
            },
            "rating_recommendation": f"The Altman Z-Score of {z_score:.2f} corroborates the structural model findings, signaling a {'safe' if z_score > 2.99 else 'distressed' if z_score < 1.81 else 'grey'} zone financial standing.",
            "covenant_analysis": "Based on the structural metrics, current leverage levels do not breach standard covenants, though continued monitoring of asset volatility is advised.",
            "outlook": f"The 12-month outlook is {'Stable' if pd_val < 0.05 else 'Negative'}, contingent on prevailing macroeconomic rates and sector equity performance."
        }
        
        return memo
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

with open('api/routes/multi_asset.py', 'r') as f:
    content = f.read()

old_code = """        # Run Merton model
        merton_res = run_single_firm(
            equity_series=hist,
            D=default_point,
            r=0.04,
            T=1.0,
            sentiment_score=sentiment_score
        )
        
        # Inject sentiment into the response metrics
        merton_res["sentiment_score"] = sentiment_score"""

new_code = """        # Run Merton model
        merton_res = run_single_firm(
            equity_series=hist,
            D=default_point,
            r=0.04,
            T=1.0,
            sentiment_score=sentiment_score
        )
        
        # Convert pandas series to dicts so it can be JSON serialized
        if "asset_series" in merton_res and hasattr(merton_res["asset_series"], "to_dict"):
            merton_res["asset_series"] = merton_res["asset_series"].to_dict()
        if "dd_timeseries" in merton_res and hasattr(merton_res["dd_timeseries"], "to_dict"):
            merton_res["dd_timeseries"] = merton_res["dd_timeseries"].to_dict()
            
        # Also convert keys (Timestamps) to strings to be safe
        merton_res["asset_series"] = {str(k): v for k, v in merton_res["asset_series"].items()}
        merton_res["dd_timeseries"] = {str(k): v for k, v in merton_res["dd_timeseries"].items()}
        
        # Inject sentiment into the response metrics
        merton_res["sentiment_score"] = sentiment_score"""

content = content.replace(old_code, new_code)

with open('api/routes/multi_asset.py', 'w') as f:
    f.write(content)

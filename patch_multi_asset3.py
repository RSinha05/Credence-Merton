with open('api/routes/multi_asset.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "merton_res = run_single_firm" in line:
        pass # keep it
    if "merton_res[\"sentiment_score\"] = sentiment_score" in line:
        # inject just before this
        new_lines.insert(-1, "        # Convert pandas series to dicts so it can be JSON serialized\n")
        new_lines.insert(-1, "        if 'asset_series' in merton_res and hasattr(merton_res['asset_series'], 'to_dict'):\n")
        new_lines.insert(-1, "            merton_res['asset_series'] = {str(k): v for k, v in merton_res['asset_series'].to_dict().items()}\n")
        new_lines.insert(-1, "        if 'dd_timeseries' in merton_res and hasattr(merton_res['dd_timeseries'], 'to_dict'):\n")
        new_lines.insert(-1, "            merton_res['dd_timeseries'] = {str(k): v for k, v in merton_res['dd_timeseries'].to_dict().items()}\n")

with open('api/routes/multi_asset.py', 'w') as f:
    f.writelines(new_lines)

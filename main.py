#!/usr/bin/env python3
"""main.py — Merton/KMV Distance-to-Default Credit Risk Model

End-to-end pipeline: data acquisition → VK iteration → DD/PD computation → validation → visualization.
"""

import logging
import os
import sys
import pandas as pd

# Add the current directory to sys.path to ensure absolute imports work
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config import (
    FIRM_PANEL, OUTPUT_DIR, T_HORIZON, VK_MAX_ITER, VK_TOL,
    PD_TERM_HORIZONS, get_tickers
)
from data.equity import fetch_equity_data, compute_equity_volatility
from data.edgar import SECEdgarClient
from data.risk_free import fetch_risk_free_rate
from data.ratings import get_ratings_panel
from model.merton import run_single_firm
from model.validation import compute_spearman_correlation, build_validation_table
from visualization.plots import (
    plot_dd_time_series, plot_pd_vs_rating,
    plot_asset_vs_barrier, plot_pd_term_structure
)

logger = logging.getLogger(__name__)


def main():
    # 1. Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s'
    )

    # 2. Print banner
    print("=" * 70)
    print("  Credence-MertonX: Merton/KMV Distance-to-Default Model")
    print("  Equity-as-a-Call-Option Structural Credit Risk Framework")
    print("=" * 70)

    # Ensure output dir exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 3. Fetch risk-free rate
    r = fetch_risk_free_rate()
    logger.info(f"Using Risk-Free Rate: {r:.4f} ({r:.2%})")

    # 4. Initialize SECEdgarClient
    client = SECEdgarClient()

    # Results containers
    dd_series_dict = {}       # {ticker: DD time series}
    asset_series_dict = {}    # {ticker: V_t asset value series}
    default_points = {}       # {ticker: D (default point)}
    pd_terms = {}             # {ticker: {T: PD}}
    raw_results = []          # List of (firm_entry, result_dict) for validation
    successful_firms = []     # Firm entries that succeeded

    # 5. Process each firm
    for firm in FIRM_PANEL:
        ticker = firm.ticker
        logger.info(f"{'─' * 50}")
        logger.info(f"Processing: {ticker} ({firm.name}) | Rating: {firm.sp_rating}")

        try:
            # 5a. Fetch equity data
            equity_df = fetch_equity_data(ticker)
            mkt_cap_series = equity_df.set_index('date')['mkt_cap']
            mkt_cap_series = mkt_cap_series.dropna()
            equity_vol = compute_equity_volatility(equity_df['log_return'])
            logger.info(f"  Equity vol (σ_E): {equity_vol:.4f}, Latest mkt cap: ${mkt_cap_series.iloc[-1]:,.0f}")

            # 5b. Fetch balance sheet debt from EDGAR
            debt_data = client.extract_debt_data(ticker)
            D = debt_data['default_point']
            logger.info(f"  Default point (D): ${D:,.0f} | STD: ${debt_data.get('short_term_debt', 0):,.0f}, LTD: ${debt_data.get('long_term_debt', 0):,.0f}")

            # 5c. Run Merton model (VK iteration)
            result = run_single_firm(
                equity_series=mkt_cap_series,
                D=D,
                r=r,
                T=T_HORIZON,
                max_iter=VK_MAX_ITER,
                tol=VK_TOL
            )

            # Store results for visualization
            dd_series_dict[ticker] = result['dd_timeseries']
            asset_series_dict[ticker] = result['asset_series']
            default_points[ticker] = D
            pd_terms[ticker] = result['pd_term_structure']

            # Store for validation table
            raw_results.append(result)
            successful_firms.append(firm)

            logger.info(
                f"  ✓ Converged in {result['iterations']} iterations | "
                f"σ_V: {result['sigma_V']:.4f} | "
                f"DD(RN): {result['DD_rn']:.2f} | DD(RW): {result['DD_rw']:.2f} | "
                f"PD(RN): {result['PD_rn']:.4%} | PD(RW): {result['PD_rw']:.4%}"
            )

        except Exception as e:
            logger.error(f"  ✗ Failed to process {ticker}: {e}")
            continue

    if not raw_results:
        logger.error("No firms were successfully processed. Exiting.")
        return

    # 6. Build validation table
    logger.info(f"\n{'=' * 50}")
    logger.info(f"VALIDATION: {len(raw_results)} / {len(FIRM_PANEL)} firms processed successfully")
    logger.info(f"{'=' * 50}")

    validation_df = build_validation_table(raw_results, successful_firms)

    # Ensure the right column names for downstream functions
    if 'PD_rn' in validation_df.columns and 'pd_risk_neutral' not in validation_df.columns:
        validation_df['pd_risk_neutral'] = validation_df['PD_rn']

    print("\n" + "=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)
    print(validation_df[['ticker', 'sp_rating', 'ordinal', 'sigma_V', 'DD', 'PD_rn', 'PD_rw']].to_string(index=False))
    print()

    # 7. Compute Spearman correlation
    spearman_rho, spearman_p = compute_spearman_correlation(validation_df)
    logger.info(f"{'═' * 50}")
    logger.info(f"  SPEARMAN RANK CORRELATION (PD vs Rating Ordinal)")
    logger.info(f"  ρ = {spearman_rho:.4f}  |  p-value = {spearman_p:.4e}")
    if spearman_p < 0.05:
        logger.info(f"  ✓ Statistically significant (p < 0.05)")
    else:
        logger.info(f"  ⚠ Not statistically significant (p ≥ 0.05)")
    logger.info(f"{'═' * 50}")

    # 8. Generate visualizations
    logger.info("Generating visualizations...")
    try:
        plot_dd_time_series(dd_series_dict, OUTPUT_DIR)
        logger.info("  ✓ DD time series plot saved")

        plot_pd_vs_rating(validation_df, spearman_rho, spearman_p, OUTPUT_DIR)
        logger.info("  ✓ PD vs rating scatter saved")

        plot_asset_vs_barrier(asset_series_dict, default_points, OUTPUT_DIR)
        logger.info("  ✓ Asset vs barrier plot saved")

        plot_pd_term_structure(pd_terms, OUTPUT_DIR)
        logger.info("  ✓ PD term structure plot saved")

        logger.info(f"All visualizations saved to: {OUTPUT_DIR}")
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")

    # 9. Export results
    out_csv = os.path.join(OUTPUT_DIR, 'results_summary.csv')
    validation_df.to_csv(out_csv, index=False)
    logger.info(f"Results exported to: {out_csv}")

    # 10. Print final summary
    print("\n" + "=" * 70)
    print("  MODEL DIAGNOSTICS")
    print("=" * 70)
    print(f"  Firms analyzed:           {len(raw_results)}")
    print(f"  Spearman ρ:               {spearman_rho:.4f}")
    print(f"  Spearman p-value:         {spearman_p:.4e}")
    print(f"  Risk-free rate used:      {r:.4%}")
    print(f"  Time horizon (T):         {T_HORIZON} year(s)")
    print(f"  Output directory:         {OUTPUT_DIR}")
    print("=" * 70)

    # Caveat
    print("\n⚠  CAVEAT: PD = N(-DD) assumes normally distributed asset returns,")
    print("   which understates real-world default rates (fat tails). Moody's KMV")
    print("   maps DD → empirical EDF via a proprietary default database.")
    print("   N(-DD) is the best available proxy without that database.\n")


if __name__ == '__main__':
    main()

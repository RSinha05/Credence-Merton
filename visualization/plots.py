import logging
import os
from typing import Dict
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

# Style configuration
sns.set_theme(style="darkgrid")
plt.rcParams.update({'figure.autolayout': True})

def plot_dd_time_series(
    dd_series_dict: Dict[str, pd.Series],
    output_dir: str
) -> plt.Figure:
    """
    Plot Distance-to-Default (DD) time series for multiple firms.
    
    Args:
        dd_series_dict: Dictionary mapping tickers to their DD time series
        output_dir: Directory to save the plot
        
    Returns:
        The generated matplotlib Figure
    """
    logger.info("Generating DD time series plot")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for ticker, series in dd_series_dict.items():
        ax.plot(series.index, series.values, label=ticker, linewidth=1.5)
        
    # Reference lines
    ax.axhline(y=2, color='red', linestyle='--', alpha=0.7, label='DD=2 (High Risk)')
    ax.axhline(y=4, color='green', linestyle='--', alpha=0.7, label='DD=4 (Safe)')
    
    ax.set_title('Distance-to-Default Time Series', fontsize=14, pad=15)
    ax.set_xlabel('Date')
    ax.set_ylabel('Distance-to-Default (DD)')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'dd_time_series.png')
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return fig

def plot_pd_vs_rating(
    results_df: pd.DataFrame,
    spearman_rho: float,
    spearman_p: float,
    output_dir: str
) -> plt.Figure:
    """
    Plot Implied PD versus Credit Rating ordinal to validate the model.
    
    Args:
        results_df: DataFrame containing 'ticker', 'ordinal', 'pd_risk_neutral', 'sp_rating'
        spearman_rho: Spearman correlation coefficient
        spearman_p: p-value of the correlation
        output_dir: Directory to save the plot
        
    Returns:
        The generated matplotlib Figure
    """
    logger.info("Generating Implied PD vs Rating plot")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sort dataframe by ordinal to get unique sorted ratings for x-axis
    sorted_df = results_df.sort_values('ordinal').drop_duplicates('ordinal')
    
    ax.scatter(results_df['ordinal'], results_df['pd_risk_neutral'], 
               alpha=0.7, s=100, c='steelblue', edgecolor='white')
               
    ax.set_yscale('log')
    
    # Annotate points with tickers
    for idx, row in results_df.iterrows():
        ax.annotate(row['ticker'], 
                    (row['ordinal'], row['pd_risk_neutral']),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=9)
                    
    # Annotation for correlation
    textstr = f'Spearman $\\rho$: {spearman_rho:.3f}\n$p$-value: {spearman_p:.3e}'
    props = dict(boxstyle='round', facecolor='white', alpha=0.8)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)
            
    ax.set_xticks(sorted_df['ordinal'])
    ax.set_xticklabels(sorted_df['sp_rating'], rotation=45)
    
    ax.set_title('Implied PD vs. Credit Rating — Model Validation', fontsize=14, pad=15)
    ax.set_xlabel('Standard & Poor\'s Credit Rating')
    ax.set_ylabel('Implied Probability of Default (Log Scale)')
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'pd_vs_rating.png')
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return fig

def plot_asset_vs_barrier(
    asset_series_dict: Dict[str, pd.Series],
    default_points: Dict[str, float],
    output_dir: str
) -> plt.Figure:
    """
    Plot implied asset value series vs default barrier for representative firms.
    
    Args:
        asset_series_dict: Dictionary mapping tickers to asset value (V_t) time series
        default_points: Dictionary mapping tickers to default point (D)
        output_dir: Directory to save the plot
        
    Returns:
        The generated matplotlib Figure
    """
    logger.info("Generating Asset Value vs Default Barrier plot")
    
    # Pick first 4 firms
    tickers = list(asset_series_dict.keys())[:4]
    n_plots = len(tickers)
    
    if n_plots == 0:
        logger.warning("No data for asset vs barrier plot")
        fig, ax = plt.subplots()
        return fig
        
    fig, axes = plt.subplots(n_plots, 1, figsize=(10, 3 * n_plots), sharex=True)
    if n_plots == 1:
        axes = [axes]
        
    for i, ticker in enumerate(tickers):
        ax = axes[i]
        series = asset_series_dict[ticker]
        D = default_points[ticker]
        
        ax.plot(series.index, series.values, color='navy', label='Asset Value ($V_t$)')
        ax.axhline(y=D, color='red', linestyle='--', label='Default Barrier ($D$)')
        
        # Shade area below D
        ax.fill_between(series.index, series.values, D, 
                        where=(series.values < D),
                        color='red', alpha=0.3, interpolate=True)
        ax.axhspan(0, D, color='red', alpha=0.1)
        
        ax.set_title(f'{ticker}', fontsize=12)
        ax.set_ylabel('Value')
        ax.legend(loc='upper right')
        
    axes[-1].set_xlabel('Date')
    fig.suptitle('Implied Asset Value vs. Default Barrier', fontsize=14, y=1.02)
    fig.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'asset_vs_barrier.png')
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return fig

def plot_pd_term_structure(
    pd_terms: Dict[str, Dict[float, float]],
    output_dir: str
) -> plt.Figure:
    """
    Plot Probability of Default term structure for multiple firms.
    
    Args:
        pd_terms: Dictionary mapping tickers to dict of {horizon: pd}
        output_dir: Directory to save the plot
        
    Returns:
        The generated matplotlib Figure
    """
    logger.info("Generating PD Term Structure plot")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    markers = ['o', 's', '^', 'D', 'v', 'p', '*', '+', 'x']
    
    for i, (ticker, term_dict) in enumerate(pd_terms.items()):
        horizons = sorted(term_dict.keys())
        pds = [term_dict[h] for h in horizons]
        
        marker = markers[i % len(markers)]
        ax.plot(horizons, pds, marker=marker, label=ticker, linewidth=1.5, markersize=8)
        
    ax.set_yscale('log')
    ax.set_title('Probability of Default Term Structure', fontsize=14, pad=15)
    ax.set_xlabel('Horizon $T$ (Years)')
    ax.set_ylabel('Probability of Default (Log Scale)')
    ax.set_xticks(horizons)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'pd_term_structure.png')
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return fig

import logging
import numpy as np
import pandas as pd
from tslearn.clustering import TimeSeriesKMeans
from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from tslearn.utils import to_time_series_dataset
from typing import Dict, List, Optional, Tuple, Any
import json
import os

logger = logging.getLogger(__name__)

class DDTrajectoryClusterer:
    """Clusters DD time-series trajectories using DTW + K-Means to detect 
    deterioration patterns ahead of rating downgrades.
    
    A point-in-time structural model might miss a firm whose DD drops from 
    6.0 to 3.0 rapidly. This clusterer leverages Dynamic Time Warping (DTW) 
    to group trajectories based on shape, capturing the momentum of credit 
    deterioration that precedes actual defaults or downgrades.
    """

    def __init__(self, n_clusters: int = 4, window_size: int = 90, metric: str = 'dtw', random_state: int = 42) -> None:
        """Initialize the trajectory clusterer.
        
        Args:
            n_clusters (int): Number of clusters to form.
            window_size (int): Number of time steps to consider in the trajectory.
            metric (str): Distance metric to use for clustering ('dtw' or 'softdtw').
            random_state (int): Random seed for clustering algorithms.
        """
        self.n_clusters = n_clusters
        self.window_size = window_size
        self.metric = metric
        self.random_state = random_state
        self.model: Optional[TimeSeriesKMeans] = None
        self.cluster_names: Dict[int, str] = {}
        self.is_fitted: bool = False
        self.centroids: Optional[np.ndarray] = None
        self.scaler = TimeSeriesScalerMeanVariance()

    def prepare_trajectories(self, dd_series_dict: Dict[str, pd.Series], window_size: Optional[int] = None) -> Tuple[np.ndarray, List[str]]:
        """Preprocesses a dictionary of time series for tslearn consumption.
        
        Args:
            dd_series_dict (Dict[str, pd.Series]): Mapping of ticker to Distance-to-Default series.
            window_size (Optional[int]): Custom window size, overriding instance default.
            
        Returns:
            Tuple[np.ndarray, List[str]]: tslearn compatible dataset and list of aligned tickers.
        """
        ws = window_size or self.window_size
        tickers = []
        series_list = []
        
        for ticker, series in dd_series_dict.items():
            if series.empty:
                continue
                
            # Take last 'ws' elements
            s = series.tail(ws).copy()
            
            # Handle missing values via ffill and bfill
            s = s.ffill().bfill()
            
            # Pad if shorter than window size
            if len(s) < ws:
                pad_length = ws - len(s)
                # Pad with the last known value
                pad_series = pd.Series([s.iloc[-1]] * pad_length, index=[s.index[-1]] * pad_length)
                s = pd.concat([pad_series, s])
                
            series_list.append(s.values)
            tickers.append(ticker)
            
        dataset = to_time_series_dataset(series_list)
        dataset_scaled = self.scaler.fit_transform(dataset)
        
        return dataset_scaled, tickers

    def fit(self, dd_series_dict: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Fit the DTW K-Means clustering model to the trajectories and interpret clusters.
        
        Args:
            dd_series_dict (Dict[str, pd.Series]): Dictionary of firm trajectories.
            
        Returns:
            Dict[str, Any]: Contains labels mapping, cluster names mapping, centroids, and inertia.
        """
        try:
            dataset, tickers = self.prepare_trajectories(dd_series_dict)
            
            self.model = TimeSeriesKMeans(
                n_clusters=self.n_clusters, 
                metric=self.metric, 
                max_iter=50, 
                random_state=self.random_state
            )
            
            labels = self.model.fit_predict(dataset)
            self.centroids = self.model.cluster_centers_
            self.is_fitted = True
            
            # Characterize clusters based on the centroids
            cluster_characteristics = []
            for i in range(self.n_clusters):
                centroid = self.centroids[i].ravel()
                mean_val = np.mean(centroid)
                slope = np.polyfit(range(len(centroid)), centroid, 1)[0]
                cluster_characteristics.append({'id': i, 'mean': mean_val, 'slope': slope})
            
            # Assign logical names based on characteristics
            self.cluster_names = {}
            unassigned = list(range(self.n_clusters))
            
            # 1. Deteriorating: most negative slope
            det_id = min(cluster_characteristics, key=lambda x: x['slope'])['id']
            self.cluster_names[det_id] = 'Deteriorating'
            unassigned.remove(det_id)
            
            # 2. Improving: most positive slope
            if unassigned:
                imp_id = max([c for c in cluster_characteristics if c['id'] in unassigned], key=lambda x: x['slope'])['id']
                self.cluster_names[imp_id] = 'Improving'
                unassigned.remove(imp_id)
            
            # 3. Stable-Safe & Stable-Risky
            if len(unassigned) == 2:
                id1, id2 = unassigned
                mean1 = next(c['mean'] for c in cluster_characteristics if c['id'] == id1)
                mean2 = next(c['mean'] for c in cluster_characteristics if c['id'] == id2)
                
                if mean1 > mean2:
                    self.cluster_names[id1] = 'Stable-Safe'
                    self.cluster_names[id2] = 'Stable-Risky'
                else:
                    self.cluster_names[id2] = 'Stable-Safe'
                    self.cluster_names[id1] = 'Stable-Risky'
            elif len(unassigned) == 1:
                self.cluster_names[unassigned[0]] = 'Stable'
                
            labels_dict = {ticker: int(label) for ticker, label in zip(tickers, labels)}
            logger.info("Model fitted successfully.")
            
            return {
                'labels': labels_dict,
                'cluster_names': self.cluster_names,
                'centroids': self.centroids,
                'inertia': self.model.inertia_
            }
        except Exception as e:
            logger.error(f"Error fitting clusterer: {str(e)}")
            raise

    def predict_single(self, dd_series: pd.Series, ticker: str = 'unknown') -> Dict[str, Any]:
        """Classify a single firm's DD trajectory and assign an alert level.
        
        Args:
            dd_series (pd.Series): Time series of Distance-to-Default values.
            ticker (str): Ticker identifier for the firm.
            
        Returns:
            Dict[str, Any]: Prediction details and alerts.
        """
        if not self.is_fitted or self.model is None:
            raise ValueError("Clusterer must be fitted before predict.")
            
        try:
            dd_dict = {ticker: dd_series}
            dataset, _ = self.prepare_trajectories(dd_dict)
            
            cluster_id = int(self.model.predict(dataset)[0])
            cluster_name = self.cluster_names.get(cluster_id, "Unknown")
            
            # Compute actual slope and mean on recent window
            ws = self.window_size
            recent = dd_series.tail(ws).ffill().bfill()
            vals = recent.values
            if len(vals) < 2:
                slope = 0.0
            else:
                slope = np.polyfit(range(len(vals)), vals, 1)[0]
                
            mean_dd = np.mean(vals)
            is_deteriorating = slope < -0.01  # Threshold for deterioration
            
            # Assign Alert Level
            if is_deteriorating and mean_dd < 3.0:
                alert = 'critical'
            elif is_deteriorating and mean_dd >= 3.0:
                alert = 'warning'
            elif not is_deteriorating and mean_dd < 3.0:
                alert = 'watch'
            else:
                alert = 'none'
                
            return {
                'ticker': ticker,
                'cluster_id': cluster_id,
                'cluster_name': cluster_name,
                'is_deteriorating': is_deteriorating,
                'slope': slope,
                'alert_level': alert
            }
        except Exception as e:
            logger.error(f"Error predicting single trajectory: {str(e)}")
            raise

    def generate_alerts(self, dd_series_dict: Dict[str, pd.Series]) -> List[Dict[str, Any]]:
        """Generate alerts for firms exhibiting high risk or deterioration.
        
        Args:
            dd_series_dict (Dict[str, pd.Series]): Dictionary of firm trajectories.
            
        Returns:
            List[Dict[str, Any]]: Sorted list of active alerts.
        """
        if not self.is_fitted:
            self.fit(dd_series_dict)
            
        alerts = []
        for ticker, series in dd_series_dict.items():
            pred = self.predict_single(series, ticker)
            
            if pred['alert_level'] in ['warning', 'critical']:
                recent_vals = series.tail(self.window_size).values
                
                alert_dict = {
                    'ticker': ticker,
                    'cluster_name': pred['cluster_name'],
                    'alert_level': pred['alert_level'],
                    'recent_dd_mean': float(np.mean(recent_vals)),
                    'dd_slope': float(pred['slope']),
                    'recommendation': 'Immediate credit review required.' if pred['alert_level'] == 'critical' else 'Place on internal watch list.'
                }
                alerts.append(alert_dict)
                
        # Sort by severity (critical first) then by slope (most negative first)
        alerts.sort(key=lambda x: (0 if x['alert_level'] == 'critical' else 1, x['dd_slope']))
        return alerts

    def generate_demo_trajectories(self, n_firms: int = 20, window_size: int = 90, seed: int = 42) -> Dict[str, pd.Series]:
        """Generate synthetic Distance-to-Default trajectories for clustering demonstration.
        
        Args:
            n_firms (int): Total number of firms to simulate (should be multiple of 4).
            window_size (int): Length of the time series.
            seed (int): Random seed for reproducibility.
            
        Returns:
            Dict[str, pd.Series]: Mapping of simulated tickers to their DD trajectories.
        """
        np.random.seed(seed)
        
        firms_per_group = max(1, n_firms // 4)
        trajectories = {}
        idx = 0
        
        dates = pd.date_range(end=pd.Timestamp.today(), periods=window_size, freq='B')
        
        # Group 1: Stable-Safe (High DD)
        for _ in range(firms_per_group):
            base = np.random.uniform(5.0, 7.0)
            noise = np.random.normal(0, 0.1, window_size)
            path = base + np.cumsum(noise) # Random walk
            path = np.clip(path, 4.0, 10.0)
            trajectories[f'FIRM_SAFE_{idx}'] = pd.Series(path, index=dates)
            idx += 1
            
        # Group 2: Stable-Risky (Low DD)
        for _ in range(firms_per_group):
            base = np.random.uniform(1.5, 3.0)
            noise = np.random.normal(0, 0.1, window_size)
            path = base + np.cumsum(noise)
            path = np.clip(path, 0.5, 3.5)
            trajectories[f'FIRM_RISKY_{idx}'] = pd.Series(path, index=dates)
            idx += 1
            
        # Group 3: Deteriorating (Starts high, trends low)
        for _ in range(firms_per_group):
            base = np.random.uniform(5.0, 6.0)
            trend = np.linspace(0, -np.random.uniform(3.0, 4.5), window_size)
            noise = np.random.normal(0, 0.2, window_size)
            path = base + trend + noise
            trajectories[f'FIRM_DET_{idx}'] = pd.Series(path, index=dates)
            idx += 1
            
        # Group 4: Improving (Starts low, trends high)
        for _ in range(firms_per_group):
            base = np.random.uniform(1.0, 2.0)
            trend = np.linspace(0, np.random.uniform(3.0, 4.5), window_size)
            noise = np.random.normal(0, 0.2, window_size)
            path = base + trend + noise
            trajectories[f'FIRM_IMP_{idx}'] = pd.Series(path, index=dates)
            idx += 1
            
        return trajectories

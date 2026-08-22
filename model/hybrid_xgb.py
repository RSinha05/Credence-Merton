import logging
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import LabelEncoder
from typing import Dict, List, Optional, Tuple, Any
import json
import os

logger = logging.getLogger(__name__)

class HybridPDClassifier:
    """XGBoost-based hybrid classifier combining structural and fundamental signals.
    
    This module implements a hybrid PD classifier that fuses market-implied signals 
    (Merton Distance to Default) with accounting fundamentals (Altman Z-Score components).
    This mirrors production models used in industry by blending structural and statistical 
    signals to produce robust Probability of Default (PD) estimates.
    """

    def __init__(self) -> None:
        """Initialize the hybrid PD classifier."""
        self.model: Optional[xgb.XGBClassifier] = None
        self.feature_names: List[str] = []
        self.is_fitted: bool = False
        self.feature_importances: Dict[str, float] = {}

    def build_feature_vector(self, merton_results: dict, altman_results: dict, macro: Optional[dict] = None) -> Dict[str, float]:
        """Builds a flat feature vector from Merton, Altman, and macroeconomic signals.
        
        Args:
            merton_results (dict): Dictionary containing Merton model outputs (e.g. DD_rn, sigma_V).
            altman_results (dict): Dictionary containing Altman Z-score outputs (e.g. z_score, x1, x2).
            macro (Optional[dict]): Optional dictionary containing macro variables (e.g. risk_free_rate).
            
        Returns:
            Dict[str, float]: Flattened dictionary of features.
        """
        features: Dict[str, float] = {}
        
        # Extract Merton features
        features['DD_rn'] = float(merton_results.get('DD_rn', 0.0))
        features['DD_rw'] = float(merton_results.get('DD_rw', 0.0))
        features['PD_rn'] = float(merton_results.get('PD_rn', 0.0))
        features['PD_rw'] = float(merton_results.get('PD_rw', 0.0))
        features['sigma_V'] = float(merton_results.get('sigma_V', 0.0))
        features['V_current'] = float(merton_results.get('V_current', 0.0))
        features['iterations'] = float(merton_results.get('iterations', 0.0))
        
        # Extract Altman features
        features['z_score'] = float(altman_results.get('z_score', 0.0))
        features['z_pp_score'] = float(altman_results.get('z_pp_score', 0.0))
        features['x1'] = float(altman_results.get('x1', 0.0))
        features['x2'] = float(altman_results.get('x2', 0.0))
        features['x3'] = float(altman_results.get('x3', 0.0))
        features['x4'] = float(altman_results.get('x4', 0.0))
        features['x5'] = float(altman_results.get('x5', 0.0))
        
        # Extract Macro features
        if macro:
            features['risk_free_rate'] = float(macro.get('risk_free_rate', 0.0))
            features['yield_spread'] = float(macro.get('yield_spread', 0.0))
        
        # Derived features
        z_score = features['z_score']
        dd_rn = features['DD_rn']
        
        features['dd_z_ratio'] = float(dd_rn / z_score) if z_score != 0 else 0.0
        features['dd_times_sigma'] = float(dd_rn * features['sigma_V'])
        features['leverage_adjusted_dd'] = float(dd_rn * (features['x4'] if features['x4'] > 0 else 1.0))
        
        return features

    def fit(self, features_df: pd.DataFrame, labels: Optional[pd.Series] = None, rating_ordinals: Optional[pd.Series] = None) -> Dict[str, Any]:
        """Fit the XGBoost classifier with cross-validation.
        
        Args:
            features_df (pd.DataFrame): DataFrame of feature vectors.
            labels (Optional[pd.Series]): Binary series indicating default (1) or healthy (0).
            rating_ordinals (Optional[pd.Series]): Optional rating ordinals used as proxy if labels are missing.
            
        Returns:
            Dict[str, Any]: Dictionary containing training metrics and feature importances.
            
        Raises:
            ValueError: If neither labels nor rating_ordinals are provided.
        """
        try:
            if labels is None:
                if rating_ordinals is not None:
                    logger.warning("No explicit default labels provided. Using rating ordinals as a proxy (>= 6 is distressed).")
                    labels = (rating_ordinals >= 6).astype(int)
                else:
                    raise ValueError("Either labels or rating_ordinals must be provided to fit the model.")
            
            self.feature_names = list(features_df.columns)
            X = features_df.values
            y = labels.values
            
            # Setup cross validation
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            
            self.model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.1,
                eval_metric='logloss',
                use_label_encoder=False,
                random_state=42
            )
            
            cv_scores = []
            for train_idx, val_idx in skf.split(X, y):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]
                
                self.model.fit(X_train, y_train)
                y_pred_proba = self.model.predict_proba(X_val)[:, 1]
                auc = roc_auc_score(y_val, y_pred_proba)
                cv_scores.append(auc)
                
            cv_auc_mean = float(np.mean(cv_scores))
            cv_auc_std = float(np.std(cv_scores))
            
            # Retrain on full data
            self.model.fit(X, y)
            self.is_fitted = True
            
            importances = self.model.feature_importances_
            feature_imp = {name: float(imp) for name, imp in zip(self.feature_names, importances)}
            self.feature_importances = dict(sorted(feature_imp.items(), key=lambda item: item[1], reverse=True))
            
            logger.info(f"Model fitted successfully. Mean CV AUC: {cv_auc_mean:.4f}")
            
            return {
                'cv_auc_mean': cv_auc_mean,
                'cv_auc_std': cv_auc_std,
                'feature_importances': self.feature_importances,
                'n_samples': len(X)
            }
        except Exception as e:
            logger.error(f"Error fitting model: {str(e)}")
            raise

    def predict_pd(self, features: dict) -> Dict[str, Any]:
        """Predict probability of default and determine risk tier.
        
        Args:
            features (dict): Dictionary of features for a single firm.
            
        Returns:
            Dict[str, Any]: Dictionary containing PD, risk tier, and top drivers.
            
        Raises:
            ValueError: If the model is not fitted.
        """
        if not self.is_fitted or self.model is None:
            raise ValueError("Model must be fitted before calling predict.")
            
        try:
            # Create a dataframe to ensure feature alignment
            X = pd.DataFrame([features])[self.feature_names]
            
            pd_prob = float(self.model.predict_proba(X)[0, 1])
            
            if pd_prob < 0.01:
                risk_tier = 'Minimal Risk'
            elif pd_prob < 0.05:
                risk_tier = 'Low Risk'
            elif pd_prob < 0.15:
                risk_tier = 'Moderate Risk'
            elif pd_prob < 0.30:
                risk_tier = 'High Risk'
            else:
                risk_tier = 'Distressed'
                
            # Get top drivers based on global feature importance
            drivers = []
            for feat in list(self.feature_importances.keys())[:5]:
                if feat in features:
                    drivers.append({'feature': feat, 'value': features[feat], 'importance': self.feature_importances[feat]})
            top_drivers = sorted(drivers, key=lambda x: x['importance'], reverse=True)[:3]
            
            return {
                'hybrid_pd': pd_prob,
                'risk_tier': risk_tier,
                'top_drivers': top_drivers
            }
        except Exception as e:
            logger.error(f"Error predicting PD: {str(e)}")
            raise

    def save(self, filepath: str) -> None:
        """Save the XGBoost model and metadata.
        
        Args:
            filepath (str): Base path for saving the model (without extension).
        """
        if not self.is_fitted or self.model is None:
            raise ValueError("Cannot save an unfitted model.")
            
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            model_path = f"{filepath}.json"
            meta_path = f"{filepath}_meta.json"
            
            self.model.save_model(model_path)
            
            metadata = {
                'feature_names': self.feature_names,
                'feature_importances': self.feature_importances
            }
            with open(meta_path, 'w') as f:
                json.dump(metadata, f)
                
            logger.info(f"Model saved to {model_path} and metadata to {meta_path}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise

    def load(self, filepath: str) -> None:
        """Load the XGBoost model and metadata.
        
        Args:
            filepath (str): Base path from which to load the model (without extension).
        """
        try:
            model_path = f"{filepath}.json"
            meta_path = f"{filepath}_meta.json"
            
            self.model = xgb.XGBClassifier()
            self.model.load_model(model_path)
            
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
                
            self.feature_names = metadata.get('feature_names', [])
            self.feature_importances = metadata.get('feature_importances', {})
            self.is_fitted = True
            
            logger.info(f"Model loaded from {model_path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def generate_training_data(self, n_firms: int = 500, seed: int = 42) -> Tuple[pd.DataFrame, pd.Series]:
        """Generate synthetic training data replicating realistic fundamental and structural dynamics.
        
        Args:
            n_firms (int): Number of synthetic firms to generate.
            seed (int): Random seed for reproducibility.
            
        Returns:
            Tuple[pd.DataFrame, pd.Series]: DataFrame of features and a Series of binary labels.
        """
        np.random.seed(seed)
        
        # Assume 70% IG, 30% HY
        n_ig = int(n_firms * 0.7)
        n_hy = n_firms - n_ig
        
        # Base default rates (~2% IG, ~15% HY)
        labels_ig = np.random.binomial(1, 0.02, n_ig)
        labels_hy = np.random.binomial(1, 0.15, n_hy)
        labels = np.concatenate([labels_ig, labels_hy])
        
        features_list = []
        for i, is_default in enumerate(labels):
            is_ig = i < n_ig
            
            if is_ig:
                if is_default:
                    dd = np.random.normal(3.0, 1.0)
                    z_score = np.random.normal(1.5, 0.5)
                else:
                    dd = np.random.normal(6.0, 1.5)
                    z_score = np.random.normal(3.5, 0.8)
            else:
                if is_default:
                    dd = np.random.normal(1.0, 0.5)
                    z_score = np.random.normal(0.5, 0.4)
                else:
                    dd = np.random.normal(2.5, 1.0)
                    z_score = np.random.normal(1.8, 0.6)
                    
            sigma_v = np.random.uniform(0.1, 0.5) if is_ig else np.random.uniform(0.3, 0.8)
            x4 = np.random.uniform(1.0, 5.0) if is_ig else np.random.uniform(0.5, 2.0)
            
            raw_features = {
                'DD_rn': dd,
                'DD_rw': dd * 1.1,
                'PD_rn': np.exp(-dd),
                'PD_rw': np.exp(-dd * 1.1),
                'sigma_V': sigma_v,
                'V_current': np.random.lognormal(10, 1),
                'iterations': np.random.randint(5, 50),
                'z_score': z_score,
                'z_pp_score': z_score * 1.05,
                'x1': z_score * 0.2 + np.random.normal(0, 0.1),
                'x2': z_score * 0.3 + np.random.normal(0, 0.1),
                'x3': z_score * 0.4 + np.random.normal(0, 0.1),
                'x4': x4,
                'x5': z_score * 0.1 + np.random.normal(0, 0.1),
            }
            
            macro = {'risk_free_rate': 0.04, 'yield_spread': 0.015}
            feat_vec = self.build_feature_vector(raw_features, raw_features, macro)
            features_list.append(feat_vec)
            
        df = pd.DataFrame(features_list)
        y = pd.Series(labels, name="is_default")
        
        return df, y

    def fit_demo(self) -> Dict[str, Any]:
        """Convenience function to generate data and train the model immediately.
        
        Returns:
            Dict[str, Any]: Training metrics and feature importances.
        """
        logger.info("Generating synthetic training data...")
        X, y = self.generate_training_data()
        logger.info("Training demo model...")
        return self.fit(X, y)

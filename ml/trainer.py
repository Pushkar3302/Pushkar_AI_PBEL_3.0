"""
Model Trainer Module.
Trains and compares multiple machine learning algorithms:
- Random Forest Regressor
- Gradient Boosting Regressor
- XGBoost Regressor (with automatic fallback)
- Decision Tree Regressor
- Ridge / Linear Regression

Evaluates models using MAE, RMSE, and R2 metrics, selects the best model, and persists via joblib.
"""

import os
import logging
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except Exception:
    HAS_XGBOOST = False

from ml.preprocessor import MLPreprocessor

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Trainer class for comparing models and persisting the best performer."""

    def __init__(self, saved_models_dir: str = "saved_models"):
        self.saved_models_dir = saved_models_dir
        os.makedirs(self.saved_models_dir, exist_ok=True)
        self.preprocessor = MLPreprocessor()
        self.models = {
            "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
            "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
            "Decision Tree": DecisionTreeRegressor(max_depth=6, random_state=42),
            "Ridge Regression": Ridge(alpha=1.0)
        }
        if HAS_XGBOOST:
            self.models["XGBoost Regressor"] = XGBRegressor(n_estimators=100, learning_rate=0.08, random_state=42)

    def train_and_evaluate(self, df: pd.DataFrame) -> Tuple[Dict[str, Dict[str, float]], str, Any]:
        """Train all models, compute metrics, select and save the best model."""
        X_train, X_test, y_train, y_test = self.preprocessor.prepare_train_test_split(df)

        results = {}
        best_model_name = ""
        best_r2 = -float("inf")
        best_model_obj = None

        for name, model in self.models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            mae = float(mean_absolute_error(y_test, y_pred))
            rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            r2 = float(r2_score(y_test, y_pred))

            results[name] = {
                "MAE": round(mae, 3),
                "RMSE": round(rmse, 3),
                "R2": round(r2, 4)
            }

            if r2 > best_r2:
                best_r2 = r2
                best_model_name = name
                best_model_obj = model

        # Save Best Model and Scaler
        model_path = os.path.join(self.saved_models_dir, "best_model.pkl")
        scaler_path = os.path.join(self.saved_models_dir, "scaler.pkl")

        joblib.dump({"name": best_model_name, "model": best_model_obj}, model_path)
        joblib.dump(self.preprocessor.scaler, scaler_path)

        logger.info(f"Best Model Selected: {best_model_name} with R2: {best_r2:.4f}")
        return results, best_model_name, best_model_obj

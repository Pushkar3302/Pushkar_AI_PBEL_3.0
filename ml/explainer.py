"""
Explainable AI (SHAP) Explainer Module.
Generates local and global feature importance breakdowns using SHAP values.
"""

import logging
import numpy as np
import pandas as pd
import shap
from typing import Dict, Any, List

from ml.predictor import ModelPredictor
from ml.preprocessor import MLPreprocessor

logger = logging.getLogger(__name__)


class SHAPExplainer:
    """SHAP Explainer class to extract top contributing features for any prediction."""

    def __init__(self, predictor: ModelPredictor):
        self.predictor = predictor
        self.feature_names = MLPreprocessor.FEATURE_COLS
        self.explainer = None
        self._init_explainer()

    def _init_explainer(self):
        """Initialize SHAP explainer based on model type."""
        try:
            model = self.predictor.model
            if hasattr(model, "predict"):
                # Use TreeExplainer for tree-based models or KernelExplainer as fallback
                try:
                    self.explainer = shap.TreeExplainer(model)
                except Exception:
                    dummy_data = np.zeros((10, len(self.feature_names)))
                    self.explainer = shap.KernelExplainer(model.predict, dummy_data)
        except Exception as e:
            logger.error(f"Error initializing SHAP explainer: {e}")

    def explain_prediction(self, student_features: Dict[str, float]) -> Dict[str, Any]:
        """Generate local SHAP explanation for a single student."""
        preprocessor = MLPreprocessor()
        preprocessor.scaler = self.predictor.scaler
        preprocessor.is_fitted = True

        X_scaled = preprocessor.transform_dict(student_features)

        try:
            if self.explainer is not None:
                shap_values = self.explainer.shap_values(X_scaled)
                if isinstance(shap_values, list):
                    shap_values = shap_values[0]
                values = shap_values[0]
            else:
                # Fallback heuristics if SHAP initialization fails
                values = self._heuristic_feature_importance(student_features)

            feature_contributions = []
            for name, val, actual_val in zip(self.feature_names, values, [student_features.get(f, 0.0) for f in self.feature_names]):
                feature_contributions.append({
                    "feature": name,
                    "impact": round(float(val), 2),
                    "value": actual_val,
                    "direction": "Positive" if val >= 0 else "Negative"
                })

            # Sort by absolute impact
            feature_contributions.sort(key=lambda x: abs(x["impact"]), reverse=True)

            return {
                "top_positive_features": [f for f in feature_contributions if f["direction"] == "Positive"][:3],
                "top_negative_features": [f for f in feature_contributions if f["direction"] == "Negative"][:3],
                "all_contributions": feature_contributions
            }
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return {
                "top_positive_features": [],
                "top_negative_features": [],
                "all_contributions": []
            }

    def _heuristic_feature_importance(self, features: Dict[str, float]) -> np.ndarray:
        """Fallback feature importance calculation."""
        att = features.get("attendance_percentage", 75)
        study = features.get("study_hours_per_week", 10)
        midterm = features.get("midterm_score", 70)
        gpa = features.get("previous_gpa", 3.0)

        return np.array([
            (att - 75) * 0.15,
            (study - 10) * 0.4,
            (gpa - 3.0) * 4.0,
            (midterm - 70) * 0.2,
            0.5, 0.5, 0.1, 0.0, 0.0
        ])

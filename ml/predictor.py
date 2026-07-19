"""
Model Predictor Module.
Executes inference on student data to predict Final Score, GPA, Grade, Pass/Fail Probability, and Risk Level.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any

from ml.preprocessor import MLPreprocessor


class ModelPredictor:
    """Predictor class for making single and batch student performance predictions."""

    def __init__(self, saved_models_dir: str = "saved_models"):
        self.saved_models_dir = saved_models_dir
        self.model_path = os.path.join(saved_models_dir, "best_model.pkl")
        self.scaler_path = os.path.join(saved_models_dir, "scaler.pkl")
        self.model = None
        self.model_name = "XGBoost Regressor"
        self.scaler = None
        self._load_model_and_scaler()

    def _load_model_and_scaler(self):
        """Load trained model and scaler from disk or train if missing."""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            data = joblib.load(self.model_path)
            self.model = data["model"]
            self.model_name = data.get("name", "XGBoost Regressor")
            self.scaler = joblib.load(self.scaler_path)
        else:
            # Generate dataset and train default model
            from ml.dataset_generator import SyntheticDatasetGenerator
            from ml.trainer import ModelTrainer

            df = SyntheticDatasetGenerator.generate_dataset(num_samples=1500)
            trainer = ModelTrainer(saved_models_dir=self.saved_models_dir)
            _, self.model_name, self.model = trainer.train_and_evaluate(df)
            self.scaler = trainer.preprocessor.scaler

    def predict_student(self, student_features: Dict[str, float]) -> Dict[str, Any]:
        """Make a complete prediction for a single student."""
        preprocessor = MLPreprocessor()
        preprocessor.scaler = self.scaler
        preprocessor.is_fitted = True

        X_scaled = preprocessor.transform_dict(student_features)
        predicted_score = float(self.model.predict(X_scaled)[0])
        predicted_score = float(np.clip(predicted_score, 0.0, 100.0))

        # Calculate GPA (0.0 - 4.0 scale)
        predicted_gpa = round(float((predicted_score / 100.0) * 4.0), 2)

        # Calculate Grade
        predicted_grade = self.calculate_grade(predicted_score)

        # Pass Probability
        pass_prob = round(float(min(1.0, max(0.0, predicted_score / 100.0 + (student_features.get("attendance_percentage", 75) - 75) / 200.0))), 2)

        # Risk Level
        risk_level = self.determine_risk_level(predicted_score, student_features.get("attendance_percentage", 75))

        # Confidence Score
        confidence = round(0.88 + (0.08 if student_features.get("attendance_percentage", 0) > 80 else 0.02), 2)

        return {
            "predicted_score": round(predicted_score, 1),
            "predicted_gpa": predicted_gpa,
            "predicted_grade": predicted_grade,
            "pass_probability": pass_prob,
            "risk_level": risk_level,
            "confidence_score": confidence,
            "model_used": self.model_name
        }

    @staticmethod
    def calculate_grade(score: float) -> str:
        """Assign letter grade based on final score."""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        return "F"

    @staticmethod
    def determine_risk_level(score: float, attendance: float) -> str:
        """Categorize student academic risk level."""
        if score < 50 or attendance < 65:
            return "CRITICAL"
        elif score < 60 or attendance < 75:
            return "HIGH"
        elif score < 75 or attendance < 85:
            return "MEDIUM"
        return "LOW"

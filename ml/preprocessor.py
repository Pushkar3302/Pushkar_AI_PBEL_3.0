"""
Data Preprocessor Module.
Handles cleaning, missing value imputation, outlier clipping, feature scaling, and encoding.
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


class MLPreprocessor:
    """Preprocessor pipeline for ML features."""

    FEATURE_COLS = [
        "attendance_percentage",
        "study_hours_per_week",
        "previous_gpa",
        "midterm_score",
        "assignment_completion",
        "quiz_score",
        "sleep_hours_per_day",
        "extracurricular",
        "internet_access"
    ]

    TARGET_COL = "final_score"

    def __init__(self):
        self.scaler = StandardScaler()
        self.is_fitted = False

    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, StandardScaler]:
        """Fit scaler and transform features."""
        df_clean = self.clean_data(df)
        X = df_clean[self.FEATURE_COLS]
        y = df_clean[self.TARGET_COL].values

        X_scaled = self.scaler.fit_transform(X)
        self.is_fitted = True
        return X_scaled, y, self.scaler

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform new data using fitted scaler."""
        if not self.is_fitted:
            raise ValueError("Preprocessor scaler is not fitted yet.")
        df_clean = self.clean_data(df)
        X = df_clean[self.FEATURE_COLS]
        return self.scaler.transform(X)

    def transform_dict(self, input_dict: dict) -> np.ndarray:
        """Transform a single sample dictionary into scaled 2D array."""
        df_single = pd.DataFrame([input_dict])
        for col in self.FEATURE_COLS:
            if col not in df_single.columns:
                df_single[col] = 0.0
        X = df_single[self.FEATURE_COLS]
        return self.scaler.transform(X)

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values and clip outliers."""
        df_copy = df.copy()

        # Fill missing numeric values with median
        for col in self.FEATURE_COLS:
            if col in df_copy.columns:
                if df_copy[col].isnull().sum() > 0:
                    df_copy[col] = df_copy[col].fillna(df_copy[col].median())

        # Clip outliers using IQR
        for col in ["study_hours_per_week", "attendance_percentage", "previous_gpa"]:
            if col in df_copy.columns:
                q1 = df_copy[col].quantile(0.25)
                q3 = df_copy[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                df_copy[col] = df_copy[col].clip(lower=lower, upper=upper)

        return df_copy

    def prepare_train_test_split(
        self, df: pd.DataFrame, test_size: float = 0.2, seed: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Clean, scale, and split dataset into train and test sets."""
        X_scaled, y, _ = self.fit_transform(df)
        return train_test_split(X_scaled, y, test_size=test_size, random_state=seed)

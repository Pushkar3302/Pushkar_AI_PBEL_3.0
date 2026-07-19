"""
Synthetic Dataset Generator for Student Performance Prediction.
Generates realistic academic records with natural statistical correlations.
"""

import os
import numpy as np
import pandas as pd
from typing import Tuple


class SyntheticDatasetGenerator:
    """Generates synthetic student performance datasets with realistic correlations."""

    @staticmethod
    def generate_dataset(num_samples: int = 2000, seed: int = 42) -> pd.DataFrame:
        """Generate synthetic student performance dataset."""
        np.random.seed(seed)

        # Features
        attendance = np.random.normal(loc=78, scale=12, size=num_samples)
        attendance = np.clip(attendance, 40, 100)

        study_hours = np.random.normal(loc=12, scale=5, size=num_samples)
        study_hours = np.clip(study_hours, 1, 35)

        previous_gpa = np.random.normal(loc=3.1, scale=0.5, size=num_samples)
        previous_gpa = np.clip(previous_gpa, 1.5, 4.0)

        midterm_score = (0.45 * attendance) + (0.8 * study_hours) + (8 * previous_gpa) + np.random.normal(0, 5, num_samples)
        midterm_score = np.clip(midterm_score, 20, 100)

        assignment_completion = np.random.normal(loc=82, scale=15, size=num_samples)
        assignment_completion = np.clip(assignment_completion, 30, 100)

        quiz_score = (0.3 * midterm_score) + (0.4 * assignment_completion) + np.random.normal(0, 6, num_samples)
        quiz_score = np.clip(quiz_score, 20, 100)

        sleep_hours = np.random.normal(loc=7.2, scale=1.1, size=num_samples)
        sleep_hours = np.clip(sleep_hours, 4, 10)

        extracurricular = np.random.choice([0, 1], size=num_samples, p=[0.4, 0.6])
        internet_access = np.random.choice([0, 1], size=num_samples, p=[0.1, 0.9])

        # Target: Final Score (0 - 100)
        final_score = (
            0.30 * midterm_score +
            0.25 * quiz_score +
            0.20 * (attendance / 100 * 100) +
            0.15 * (assignment_completion) +
            0.10 * (previous_gpa / 4.0 * 100) +
            np.random.normal(0, 3.5, num_samples)
        )
        final_score = np.clip(final_score, 10, 100)

        # Target: GPA (0.0 - 4.0)
        final_gpa = np.round((final_score / 100.0) * 4.0, 2)

        # Target: Grade
        grades = []
        for s in final_score:
            if s >= 90:
                grades.append("A+")
            elif s >= 85:
                grades.append("A")
            elif s >= 80:
                grades.append("B+")
            elif s >= 70:
                grades.append("B")
            elif s >= 60:
                grades.append("C")
            elif s >= 50:
                grades.append("D")
            else:
                grades.append("F")

        # Target: Pass / Fail
        passed = (final_score >= 50).astype(int)

        # Target: Risk Level
        risk_levels = []
        for score, att in zip(final_score, attendance):
            if score < 50 or att < 65:
                risk_levels.append("CRITICAL")
            elif score < 60 or att < 75:
                risk_levels.append("HIGH")
            elif score < 75 or att < 85:
                risk_levels.append("MEDIUM")
            else:
                risk_levels.append("LOW")

        df = pd.DataFrame({
            "attendance_percentage": np.round(attendance, 1),
            "study_hours_per_week": np.round(study_hours, 1),
            "previous_gpa": np.round(previous_gpa, 2),
            "midterm_score": np.round(midterm_score, 1),
            "assignment_completion": np.round(assignment_completion, 1),
            "quiz_score": np.round(quiz_score, 1),
            "sleep_hours_per_day": np.round(sleep_hours, 1),
            "extracurricular": extracurricular,
            "internet_access": internet_access,
            "final_score": np.round(final_score, 1),
            "final_gpa": final_gpa,
            "grade": grades,
            "passed": passed,
            "risk_level": risk_levels
        })

        return df

    @classmethod
    def save_default_dataset(cls, output_path: str) -> str:
        """Generate and save default dataset to file if not exists."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if not os.path.exists(output_path):
            df = cls.generate_dataset()
            df.to_csv(output_path, index=False)
        return output_path

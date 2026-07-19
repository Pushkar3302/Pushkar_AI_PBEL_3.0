"""
Unit Tests for Machine Learning & Explainable AI Pipeline.
"""

import unittest
from ml.dataset_generator import SyntheticDatasetGenerator
from ml.trainer import ModelTrainer
from ml.predictor import ModelPredictor
from ml.explainer import SHAPExplainer


class TestMLPipeline(unittest.TestCase):

    def test_dataset_generator(self):
        df = SyntheticDatasetGenerator.generate_dataset(num_samples=100)
        self.assertEqual(len(df), 100)
        self.assertIn("final_score", df.columns)
        self.assertIn("risk_level", df.columns)

    def test_model_trainer_and_predictor(self):
        df = SyntheticDatasetGenerator.generate_dataset(num_samples=200)
        trainer = ModelTrainer(saved_models_dir="tests/test_models")
        results, best_name, best_obj = trainer.train_and_evaluate(df)

        self.assertTrue(len(results) > 0)
        self.assertIn(best_name, results)
        self.assertNotEqual(best_name, "")

        predictor = ModelPredictor(saved_models_dir="tests/test_models")
        sample_features = {
            "attendance_percentage": 85.0,
            "study_hours_per_week": 15.0,
            "previous_gpa": 3.4,
            "midterm_score": 82.0,
            "assignment_completion": 90.0,
            "quiz_score": 80.0,
            "sleep_hours_per_day": 7.5,
            "extracurricular": 1,
            "internet_access": 1
        }

        pred = predictor.predict_student(sample_features)
        self.assertIn("predicted_score", pred)
        self.assertIn("predicted_gpa", pred)
        self.assertTrue(0 <= pred["predicted_score"] <= 100)

        explainer = SHAPExplainer(predictor)
        exp = explainer.explain_prediction(sample_features)
        self.assertIn("top_positive_features", exp)
        self.assertIn("all_contributions", exp)


if __name__ == "__main__":
    unittest.main()

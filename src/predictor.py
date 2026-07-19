# src/predictor.py
import joblib
import os
import pandas as pd

# Global variable to cache the model in memory once loaded
_MODEL = None

def get_model():
    """
    Loads and caches the serialized Scikit-Learn model pipeline from disk.
    """
    global _MODEL
    if _MODEL is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(project_root, "student_model.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at: {model_path}. Please execute 'train_model.py' to generate it."
            )
        _MODEL = joblib.load(model_path)
    return _MODEL

def predict_performance(features):
    """
    Performs model inference on student academic features.
    
    Parameters:
    - features (dict): Dictionary containing 'study_hours' (internal marks), 
                       'attendance_percentage', and 'mock_score'.
    
    Returns:
    - dict: Multi-class outcomes with prediction category and confidence details:
      {
          "prediction": str (e.g. "Pass", "First Class", "Outstanding", "Critical Risk", "Detained"),
          "confidence": float (probability of the predicted class, 0.0 to 1.0),
          "probabilities": dict (mapping of each class to its probability)
      }
    """
    model = get_model()
    
    # 1. Input validation
    required_features = ['study_hours', 'attendance_percentage', 'mock_score']
    for feature in required_features:
        if feature not in features:
            raise ValueError(f"Missing required input parameter: '{feature}'")
            
    # 2. Format inputs as a Pandas DataFrame to ensure feature names match the scaler/estimator schema
    input_df = pd.DataFrame([{
        'study_hours': float(features['study_hours']),
        'attendance_percentage': float(features['attendance_percentage']),
        'mock_score': float(features['mock_score'])
    }])
    
    # 3. Perform prediction and extract class labels
    prediction = model.predict(input_df)[0]
    probabilities = model.predict_proba(input_df)[0]
    classes = model.classes_
    
    # Map classes to their prediction probabilities
    prob_dict = {str(c): float(p) for c, p in zip(classes, probabilities)}
    predicted_class_prob = prob_dict.get(str(prediction), 0.0)
    
    return {
        "prediction": str(prediction),
        "confidence": float(predicted_class_prob),
        "probabilities": prob_dict
    }

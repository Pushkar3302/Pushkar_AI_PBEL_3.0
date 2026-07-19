# src/train_model.py
import sys
import os
# Ensure the project root is in the python path to prevent import errors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from src import db_manager

def populate_database_if_empty(n_samples=200):
    """
    Checks if tables are empty. If they are, populates them with synthetic student data 
    tailored to the Indian university context.
    
    Database mapping:
    - 'study_hours' column stores 'internal_marks' (Sessional marks out of 30).
    - 'attendance_percentage' stores student attendance (50% to 100%).
    - 'mock_score' stores End-Semester Mock exam score (0 to 100).
    """
    df = db_manager.get_students_with_metrics()
    
    # Check if metrics are already present
    has_metrics = len(df.dropna(subset=['mock_score'])) > 0
    
    if has_metrics:
        print("Database already contains performance metrics data. Skipping data simulation.")
        return
        
    print("Database metrics table is empty. Starting data simulation for Indian context...")
    np.random.seed(42)
    
    first_names = ["Aravind", "Priya", "Rahul", "Ananya", "Amit", "Sneha", "Rohan", "Divya", 
                   "Rajesh", "Kavita", "Sanjay", "Deepika", "Vijay", "Sunita", "Vikram", "Neha", 
                   "Sandeep", "Aishwarya", "Abhishek", "Pooja", "Manoj", "Jyoti", "Karan", "Ritu", 
                   "Aditya", "Shalini", "Harish", "Preeti", "Suresh", "Geeta"]
                   
    last_names = ["Sharma", "Verma", "Patel", "Gupta", "Singh", "Kumar", "Joshi", "Mehra", 
                  "Reddy", "Nair", "Iyer", "Choudhury", "Das", "Sen", "Rao", "Mishra", 
                  "Yadav", "Pandey", "Saxena", "Trivedi", "Banerjee", "Chatterjee", "Pillai", 
                  "Bose", "Deshmukh", "Kulkarni", "Shetty", "Gowda", "Menon", "Prasad"]
    
    inserted_count = 0
    for i in range(n_samples):
        # Generate random student name and University Roll Number format (e.g. UR20261001)
        name = f"{np.random.choice(first_names)} {np.random.choice(last_names)} (Roll: UR2026{1000 + i})"
        
        # 1. Attendance Percentage: beta distribution centered around 80%, range [50, 100]
        attendance = np.random.beta(4.5, 2.0) * 50 + 50
        attendance = float(np.clip(attendance, 50.0, 100.0))
        
        # 2. Internal / Sessional Marks: Out of 30. Centered around 21, range [5, 30]
        internal_marks = np.random.normal(21, 4.5)
        internal_marks = float(np.clip(internal_marks, 0.0, 30.0))
        
        # 3. End-Semester Mock Exam Score: Out of 100. Correlated with attendance and internals.
        base_score = (attendance * 0.4) + (internal_marks * (100.0 / 30.0) * 0.45)
        noise = np.random.normal(0, 7.0)
        mock_score = base_score + noise
        mock_score = float(np.clip(mock_score, 0.0, 100.0))
        
        # Determine prediction category based on Indian Academic rules:
        # Mandatory 75% attendance rule
        if attendance < 75.0:
            outcome = "Detained"
        else:
            # Combined score estimate (Internals 30% weight, Mock Exam 70% weight)
            total_estimate = mock_score * 0.7 + (internal_marks * (100.0 / 30.0)) * 0.3
            threshold_noise = np.random.normal(0, 1.5)
            final_grade = total_estimate + threshold_noise
            
            if final_grade < 40.0:
                outcome = "Critical Risk"
            elif final_grade < 60.0:
                outcome = "Pass"
            elif final_grade < 80.0:
                outcome = "First Class"
            else:
                outcome = "Outstanding"
        
        try:
            student_id = db_manager.add_student(name)
            
            # Map internal_marks to study_hours database column for transparent backend compatibility
            db_manager.add_performance_metrics(
                student_id=student_id,
                study_hours=internal_marks, 
                attendance_percentage=attendance,
                mock_score=mock_score,
                predicted_outcome=outcome
            )
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting student row {i+1}: {e}")
            
    print(f"Successfully generated and inserted {inserted_count} Indian academic metrics records.")

def train_and_save_model():
    """
    Retrieves data from the database, trains a Multi-class Random Forest Classifier pipeline,
    evaluates performance on a test set, and saves the trained pipeline as a pickle.
    """
    print("Retrieving student metrics from database...")
    df = db_manager.get_students_with_metrics()
    
    # Remove rows where mock_score or outcome is null
    df = df.dropna(subset=['study_hours', 'attendance_percentage', 'mock_score', 'predicted_outcome'])
    
    if len(df) == 0:
        print("No valid student data available for training. Process aborted.")
        return
        
    print(f"Loaded {len(df)} student records for training.")
    
    # Separate Features and Target
    features = ['study_hours', 'attendance_percentage', 'mock_score']
    X = df[features].astype(float)
    y = df['predicted_outcome']
    
    # 80/20 train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    
    # Classifier Pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(
            n_estimators=100, 
            max_depth=6, 
            random_state=42
        ))
    ])
    
    print("Training Random Forest Classifier (Multi-class)...")
    pipeline.fit(X_train, y_train)
    
    # Predict on test features
    y_pred = pipeline.predict(X_test)
    
    # Evaluate Pipeline
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    
    print("\n=========================================")
    print("         Model Evaluation Report         ")
    print("=========================================")
    print(f"Accuracy Score: {accuracy:.4f}")
    print("\nClassification Report Metrics:")
    print(report)
    print("=========================================\n")
    
    # Save the pipeline object at the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(project_root, "student_model.pkl")
    
    print(f"Saving trained model pipeline to: {model_path}")
    joblib.dump(pipeline, model_path)
    print("Model serialized and saved successfully.")

if __name__ == "__main__":
    db_manager.initialize_database()
    populate_database_if_empty(200)
    train_and_save_model()

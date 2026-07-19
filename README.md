# 🎓 AI-Driven Student Performance Prediction & Academic Intelligence Platform

An enterprise-grade, production-ready SaaS platform built with **Python 3.13+**, **Streamlit**, **SQLAlchemy**, **MySQL**, **XGBoost**, **SHAP**, **Plotly**, and **ReportLab**. The platform empowers educational institutions (Admins, Teachers, Students) with predictive academic analytics, early risk warning systems, explainable AI, and automated recommendations.
Alternative link:http://127.0.0.1:8505
---

## 🌟 Key Features

1. **Multi-Role Authentication & Security**:
   - Role-Based Access Control (RBAC) for **Admin**, **Teacher**, and **Student**.
   - Bcrypt password hashing, session context management, and operational audit logging.

2. **Normalized Relational Database**:
   - Fully normalized (3NF) database schema using SQLAlchemy ORM.
   - Out-of-the-box support for **MySQL** with automatic **SQLite** fallback for rapid local setup.

3. **Machine Learning & SHAP Explainable AI**:
   - Model comparative suite evaluating **Random Forest**, **Gradient Boosting**, **XGBoost**, **Decision Tree**, and **Ridge Regression**.
   - Automatic hyper-parameter evaluation using $R^2$, MAE, and RMSE metrics, saving the best model via `joblib`.
   - **SHAP (SHapley Additive exPlanations)** local and global feature importance breakdowns.

4. **AI Recommendation Engine**:
   - Contextual, rule-based and ML-driven academic action items tailored to each student's study habits and risk level.

5. **Interactive Plotly Visualizations & PDF Reports**:
   - Donut charts for risk distribution, score-vs-attendance scatter plots, radar skill matrices, and grade histograms.
   - Downloadable institutional PDF report cards generated dynamically using ReportLab.

6. **Production Infrastructure**:
   - Bulk CSV data import/export with Pydantic validation.
   - Docker & Docker-Compose setup.
   - Pytest unit testing suite.

---

## 📁 Architecture & Directory Structure

```
AI-Driven Student Performance Prediction System/
├── .env.example
├── .env
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── config/
│   ├── __init__.py
│   └── settings.py
├── database/
│   ├── __init__.py
│   ├── connection.py
│   └── models.py
├── authentication/
│   ├── __init__.py
│   ├── auth_service.py
│   └── rbac.py
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   ├── academic_service.py
│   ├── import_export_service.py
│   ├── report_service.py
│   ├── audit_service.py
│   └── notification_service.py
├── ml/
│   ├── __init__.py
│   ├── dataset_generator.py
│   ├── preprocessor.py
│   ├── trainer.py
│   ├── predictor.py
│   ├── explainer.py
│   └── recommender.py
├── saved_models/
│   ├── best_model.pkl
│   └── scaler.pkl
├── charts/
│   ├── __init__.py
│   └── plotly_charts.py
├── frontend/
│   ├── __init__.py
│   ├── components.py
│   └── views/
│       ├── auth_view.py
│       ├── admin_dashboard.py
│       ├── teacher_dashboard.py
│       ├── student_dashboard.py
│       ├── analytics_view.py
│       └── settings_view.py
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   └── test_ml.py
└── app.py
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Python 3.13 supported)
- `pip` or Virtual Environment manager

### 2. Installation & Setup

```bash
# Clone or navigate to the repository directory
cd "AI-Driven Student Performance Prediction System"

# Create a python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🔑 Default Test Credentials

The database automatically seeds default user accounts upon first launch:

| Role | Username / Email | Password | Access Privileges |
|---|---|---|---|
| **Admin** | `admin` / `admin@university.edu` | `AdminPass123` | Full System & Model Control, Audit Logs, Users |
| **Teacher** | `teacher` / `teacher@university.edu` | `TeacherPass123` | Class Analytics, Marks, Attendance, Risk Detection |
| **Student** | `student` / `student@university.edu` | `StudentPass123` | Own Predictions, SHAP Explanations, PDF Report |

---

## 🧪 Running Unit Tests

Execute the unit test suite with pytest:

```bash
pytest tests/
```

---

## 🐳 Running with Docker

```bash
docker-compose up --build
```

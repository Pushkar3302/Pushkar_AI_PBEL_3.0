"""
Visual Analytics & Insights View.
Renders Institutional Analytics for Admins/Teachers and Personal Academic Analytics for Logged-In Students.
"""

import streamlit as st
import pandas as pd
from database.connection import get_db
from database.models import RoleEnum
from authentication.rbac import rbac
from services.user_service import UserService
from services.academic_service import AcademicService
from ml.dataset_generator import SyntheticDatasetGenerator
from ml.predictor import ModelPredictor
from ml.explainer import SHAPExplainer
from charts.plotly_charts import AcademicCharts
from frontend.components import render_header, render_metric_card


def render_analytics_view():
    """Render Visual Analytics Page tailored to User Role."""
    user_role = st.session_state.get("role", "")
    user_id = st.session_state.get("user_id")

    if rbac.is_student(user_role):
        render_student_personal_analytics(user_id)
    else:
        render_institutional_analytics()


def render_student_personal_analytics(user_id: int):
    """Render Personal Analytics Insights for the logged-in Student."""
    with get_db() as db:
        student = UserService.get_student_profile(db, user_id)
        if not student:
            st.error("Student profile not found.")
            return

        user = student.user
        dept = student.department

        render_header(
            f"Personal Academic Analytics — {user.full_name if user else 'Student'}",
            f"Roll Number: {student.roll_number} • Department: {dept.code if dept else 'CS'} • Semester: {student.semester}"
        )

        summary = AcademicService.get_student_academic_summary(db, student.id)
        subject_breakdown = AcademicService.get_student_subject_breakdown(db, student.id)

        student_features = {
            "attendance_percentage": summary["avg_attendance"],
            "study_hours_per_week": student.study_hours_per_week,
            "previous_gpa": student.previous_gpa,
            "midterm_score": summary["avg_midterm"],
            "assignment_completion": summary["avg_assignment"],
            "quiz_score": summary["avg_quiz"],
            "sleep_hours_per_day": student.sleep_hours_per_day,
            "extracurricular": 1 if student.extracurricular_activities else 0,
            "internet_access": 1 if student.internet_access else 0
        }

        predictor = ModelPredictor()
        explainer = SHAPExplainer(predictor)
        prediction = predictor.predict_student(student_features)
        shap_exp = explainer.explain_prediction(student_features)

        # Personal KPI Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card("Enrolled Courses", f"{len(subject_breakdown)} Subjects", "Current Semester")
        with c2:
            render_metric_card("Overall Attendance", f"{summary['avg_attendance']}%", "Average Across Subjects")
        with c3:
            render_metric_card("Midterm & Quiz Average", f"{summary['avg_midterm']} / 100", "Assessment Avg")
        with c4:
            render_metric_card("Predicted Score & GPA", f"{prediction['predicted_score']} / 100", f"GPA: {prediction['predicted_gpa']} ({prediction['predicted_grade']})")

        st.markdown("---")

        # Row 1: Subject Bar Chart & Radar Matrix
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📊 Subject Attendance % vs Score Average")
            fig_sub_bar = AcademicCharts.plot_student_subject_performance_bar(subject_breakdown)
            st.plotly_chart(fig_sub_bar, use_container_width=True)

        with col2:
            st.markdown("#### 📈 Multi-Dimensional Radar Skill Matrix")
            fig_radar = AcademicCharts.plot_student_performance_radar(student_features)
            st.plotly_chart(fig_radar, use_container_width=True)

        st.markdown("---")

        # Row 2: SHAP Feature Importance
        st.markdown("#### 🧠 Explainable AI (SHAP) Feature Contributions for Your Prediction")
        if shap_exp.get("all_contributions"):
            fig_shap = AcademicCharts.plot_shap_waterfall_bar(shap_exp["all_contributions"])
            st.plotly_chart(fig_shap, use_container_width=True)


def render_institutional_analytics():
    """Render Institutional Visual Analytics for Admins and Teachers."""
    render_header("Institutional Visual Analytics & Insights", "Deep Exploratory Data Analysis (EDA) of Academic Performance")

    # Generate / Load dataset for visual trends
    df = SyntheticDatasetGenerator.generate_dataset(num_samples=1000)

    # Top KPI Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Analyzed Cohort", f"{len(df)} Students", "Sampled Dataset")
    with c2:
        render_metric_card("Average Final Score", f"{round(df['final_score'].mean(), 1)} / 100", "Across All Courses")
    with c3:
        render_metric_card("Overall Pass Rate", f"{round((df['passed'].mean()) * 100, 1)}%", "Passing Score >= 50%")
    with c4:
        render_metric_card("Avg Study Hours", f"{round(df['study_hours_per_week'].mean(), 1)} hrs/wk", "Self Study")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        risk_counts = df["risk_level"].value_counts().to_dict()
        fig_donut = AcademicCharts.plot_risk_distribution_donut(risk_counts)
        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        grade_counts = df["grade"].value_counts().to_dict()
        fig_grade = AcademicCharts.plot_grade_distribution_bar(grade_counts)
        st.plotly_chart(fig_grade, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔍 Correlation Scatter Analysis")
    fig_scatter = AcademicCharts.plot_attendance_vs_score_scatter(df)
    st.plotly_chart(fig_scatter, use_container_width=True)

"""
Plotly Interactive Visualizations Module.
Generates Pie, Bar, Line, Radar, Heatmap, Scatter, and SHAP Feature Importance charts.
Supports dynamic Light Mode and Dark Mode rendering.
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


class AcademicCharts:
    """Factory class for Plotly charts with dynamic Light/Dark theme support."""

    @classmethod
    def get_layout(cls) -> dict:
        """Get layout styling matching current theme_mode."""
        is_light = st.session_state.get("theme_mode") == "Light"
        font_color = "#0F172A" if is_light else "#E2E8F0"
        return dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=font_color, family="Inter, sans-serif"),
            margin=dict(l=20, r=20, t=40, b=20)
        )

    @classmethod
    def plot_risk_distribution_donut(cls, risk_counts: Dict[str, int]) -> go.Figure:
        """Create Donut Chart for Student Risk Distribution."""
        labels = list(risk_counts.keys())
        values = list(risk_counts.values())

        color_map = {
            "LOW": "#22C55E",
            "MEDIUM": "#F59E0B",
            "HIGH": "#EF4444",
            "CRITICAL": "#991B1B"
        }
        colors_list = [color_map.get(lbl, "#3B82F6") for lbl in labels]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colors_list),
            textinfo="label+percent",
            hoverinfo="label+value+percent"
        )])
        fig.update_layout(
            title="Student Risk Level Distribution",
            **cls.get_layout()
        )
        return fig

    @classmethod
    def plot_attendance_vs_score_scatter(cls, df: pd.DataFrame) -> go.Figure:
        """Scatter plot showing correlation between Attendance % and Final Score."""
        fig = px.scatter(
            df,
            x="attendance_percentage",
            y="final_score",
            color="risk_level",
            size="study_hours_per_week",
            hover_data=["previous_gpa", "midterm_score"],
            color_discrete_map={
                "LOW": "#22C55E",
                "MEDIUM": "#F59E0B",
                "HIGH": "#EF4444",
                "CRITICAL": "#991B1B"
            },
            labels={
                "attendance_percentage": "Attendance Percentage (%)",
                "final_score": "Final Score / 100",
                "risk_level": "Risk Level"
            },
            title="Attendance vs Final Performance Score"
        )
        fig.update_layout(**cls.get_layout())
        return fig

    @classmethod
    def plot_grade_distribution_bar(cls, grade_counts: Dict[str, int]) -> go.Figure:
        """Bar chart for student letter grade distribution."""
        grades = list(grade_counts.keys())
        counts = list(grade_counts.values())

        fig = px.bar(
            x=grades,
            y=counts,
            labels={"x": "Grade", "y": "Number of Students"},
            title="Overall Grade Distribution",
            color=counts,
            color_continuous_scale="Viridis"
        )
        fig.update_layout(**cls.get_layout())
        return fig

    @classmethod
    def plot_student_performance_radar(cls, student_metrics: Dict[str, float]) -> go.Figure:
        """Radar chart visualizing individual student's multi-dimension assessment scores."""
        categories = ["Attendance %", "Study Hours", "Midterm Score", "Assignments %", "Quiz Score", "Prev GPA (x25)"]
        values = [
            student_metrics.get("attendance_percentage", 75),
            min(100, student_metrics.get("study_hours_per_week", 10) * 3.5),
            student_metrics.get("midterm_score", 70),
            student_metrics.get("assignment_completion", 80),
            student_metrics.get("quiz_score", 75),
            student_metrics.get("previous_gpa", 3.0) * 25.0
        ]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Student Profile',
            line=dict(color='#3B82F6', width=2),
            fillcolor='rgba(59, 130, 246, 0.35)'
        ))
        is_light = st.session_state.get("theme_mode") == "Light"
        axis_color = "#475569" if is_light else "#94A3B8"
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], color=axis_color)
            ),
            title="Academic Capability Radar Matrix",
            **cls.get_layout()
        )
        return fig

    @classmethod
    def plot_student_subject_performance_bar(cls, subject_breakdown: List[Dict[str, Any]]) -> go.Figure:
        """Bar chart comparing Attendance % vs Subject Score Average per subject for a student."""
        subjects = [s["subject_code"] for s in subject_breakdown]
        att_scores = [s["attendance_percentage"] for s in subject_breakdown]
        avg_scores = [s["subject_average"] for s in subject_breakdown]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=subjects,
            y=att_scores,
            name='Attendance %',
            marker_color='#3B82F6'
        ))
        fig.add_trace(go.Bar(
            x=subjects,
            y=avg_scores,
            name='Subject Score Avg',
            marker_color='#10B981'
        ))
        fig.update_layout(
            barmode='group',
            title="Individual Subject Attendance % vs Score Average",
            xaxis_title="Subject Code",
            yaxis_title="Percentage / Score (0 - 100)",
            **cls.get_layout()
        )
        return fig

    @classmethod
    def plot_shap_waterfall_bar(cls, shap_contributions: List[Dict[str, Any]]) -> go.Figure:
        """Bar chart showing positive and negative SHAP feature impacts on prediction."""
        features = [item["feature"].replace("_", " ").title() for item in shap_contributions]
        impacts = [item["impact"] for item in shap_contributions]
        bar_colors = ["#22C55E" if imp >= 0 else "#EF4444" for imp in impacts]

        fig = go.Figure(go.Bar(
            x=impacts,
            y=features,
            orientation='h',
            marker=dict(color=bar_colors),
            text=[f"{imp:+.2f}" for imp in impacts],
            textposition='auto'
        ))
        fig.update_layout(
            title="Explainable AI (SHAP) Feature Contribution",
            xaxis_title="Impact on Predicted Score",
            yaxis=dict(autorange="reversed"),
            **cls.get_layout()
        )
        return fig

    @classmethod
    def plot_model_comparison_bar(cls, results: Dict[str, Dict[str, float]]) -> go.Figure:
        """Comparison bar chart of R2 scores across ML models."""
        models = list(results.keys())
        r2_scores = [results[m]["R2"] for m in models]

        fig = px.bar(
            x=models,
            y=r2_scores,
            text=r2_scores,
            labels={"x": "Model Name", "y": "R² Accuracy Score"},
            title="Model Evaluation Comparison (R² Metric)",
            color=r2_scores,
            color_continuous_scale="Blues"
        )
        fig.update_layout(**cls.get_layout())
        return fig

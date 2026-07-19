"""
AI Recommendation Engine.
Generates personalized, actionable study recommendations based on prediction metrics and SHAP feature impacts.
"""

from typing import Dict, Any, List


class RecommendationEngine:
    """Generates personalized academic action items for students."""

    @staticmethod
    def generate_recommendations(
        student_features: Dict[str, float],
        prediction_results: Dict[str, Any],
        shap_explanation: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate targeted recommendations for a student."""
        recommendations = []

        attendance = student_features.get("attendance_percentage", 80)
        study_hours = student_features.get("study_hours_per_week", 10)
        midterm = student_features.get("midterm_score", 70)
        assignment = student_features.get("assignment_completion", 80)
        sleep = student_features.get("sleep_hours_per_day", 7)
        risk = prediction_results.get("risk_level", "LOW")

        # Attendance Recommendation
        if attendance < 75:
            recommendations.append({
                "category": "Attendance",
                "priority": "HIGH",
                "title": "Increase Class Attendance Immediately",
                "description": f"Current attendance is {attendance}%. Raise attendance above 80% to lower academic risk and prevent exam eligibility warnings."
            })
        elif attendance < 85:
            recommendations.append({
                "category": "Attendance",
                "priority": "MEDIUM",
                "title": "Maintain Consistent Attendance",
                "description": f"Current attendance is {attendance}%. Aim for 90%+ for optimal concept retention and continuous assessment scores."
            })

        # Study Hours Recommendation
        if study_hours < 12:
            needed = 15 - study_hours
            recommendations.append({
                "category": "Study Habits",
                "priority": "HIGH" if study_hours < 8 else "MEDIUM",
                "title": "Boost Weekly Self-Study Hours",
                "description": f"Currently studying {study_hours} hrs/week. Increasing study time by {needed:.1f} hrs/week is estimated to boost predicted grade by 7-10%."
            })

        # Midterm / Assessment Recommendation
        if midterm < 65:
            recommendations.append({
                "category": "Academic Performance",
                "priority": "HIGH",
                "title": "Attend Faculty Remedial & Tutoring Sessions",
                "description": f"Midterm score ({midterm}%) indicates weak core subject grasp. Schedule weekly review sessions with course instructors."
            })

        # Assignment Completion Recommendation
        if assignment < 75:
            recommendations.append({
                "category": "Assignments",
                "priority": "MEDIUM",
                "title": "Submit All Pending & Practice Assignments",
                "description": f"Assignment completion rate is {assignment}%. Complete all coursework on time to claim easy continuous evaluation weightage."
            })

        # Sleep & Health Recommendation
        if sleep < 6.0:
            recommendations.append({
                "category": "Well-being",
                "priority": "MEDIUM",
                "title": "Improve Sleep Hygiene",
                "description": f"Averaging {sleep} hours of sleep per night. Aim for 7-8 hours to improve cognitive function and exam focus."
            })

        # Risk-Based Custom Rule
        if risk in ["CRITICAL", "HIGH"]:
            recommendations.append({
                "category": "Early Warning",
                "priority": "CRITICAL",
                "title": "Academic Advisor Intervention Required",
                "description": "Student flagged in High/Critical Risk category. Academic counseling session recommended prior to final exams."
            })

        if not recommendations:
            recommendations.append({
                "category": "General",
                "priority": "LOW",
                "title": "Maintain Excellent Work",
                "description": "Current performance metrics are solid. Continue existing study habits and mentor peers!"
            })

        return recommendations

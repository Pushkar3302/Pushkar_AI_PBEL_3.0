"""
Student Dashboard View.
Provides personal score/GPA predictions, individual subject attendance & marks breakdown,
SHAP Explainable AI, personalized recommendations, radar metrics, and PDF download.
"""

import streamlit as st
import pandas as pd
from database.connection import get_db
from database.models import User, StudentProfile
from services.user_service import UserService
from services.academic_service import AcademicService
from services.report_service import PDFReportService
from ml.predictor import ModelPredictor
from ml.explainer import SHAPExplainer
from ml.recommender import RecommendationEngine
from charts.plotly_charts import AcademicCharts
from frontend.components import render_header, render_metric_card


def render_student_dashboard():
    """Render Student Intelligence & Performance Dashboard."""
    user_id = st.session_state.get("user_id")

    with get_db() as db:
        student = UserService.get_student_profile(db, user_id)
        if not student:
            st.error("No student profile associated with this user account.")
            return

        user = student.user
        dept = student.department

        render_header(
            f"Welcome, {user.full_name if user else 'Student'}!",
            f"Roll Number: {student.roll_number} • Department: {dept.name if dept else 'N/A'} • Semester: {student.semester}"
        )

        # Retrieve dynamic overall academic summary & individual subject breakdown
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
        shap_explanation = explainer.explain_prediction(student_features)
        recommendations = RecommendationEngine.generate_recommendations(student_features, prediction, shap_explanation)

        # Top Metric Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card("Predicted Final Score", f"{prediction['predicted_score']} / 100", f"Overall Attendance: {summary['avg_attendance']}%")
        with col2:
            render_metric_card("Predicted GPA", f"{prediction['predicted_gpa']} / 4.0", f"Grade: {prediction['predicted_grade']}")
        with col3:
            pass_pct = int(prediction['pass_probability'] * 100)
            render_metric_card("Pass Probability", f"{pass_pct}%", "High Confidence" if pass_pct > 75 else "Low Confidence")
        with col4:
            risk = prediction['risk_level']
            color = "#34D399" if risk == "LOW" else "#FBBF24" if risk == "MEDIUM" else "#F87171"
            render_metric_card("Academic Risk Level", risk, f"AI Model: {prediction['model_used']}", delta_color=color)

        st.markdown("---")

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📚 Subject Attendance & Marks",
            "🧠 Explainable AI (SHAP)",
            "💡 Personalized Recommendations",
            "📈 Radar Skill Matrix",
            "⚙️ Update Study Habits & PDF Report"
        ])

        # TAB 1: INDIVIDUAL SUBJECT ATTENDANCE & MARKS BREAKDOWN
        with tab1:
            st.subheader("Subject-by-Subject Attendance & Marks Breakdown")

            if subject_breakdown:
                df_sub = pd.DataFrame(subject_breakdown)
                df_sub_display = df_sub[[
                    "subject_code", "subject_name", "credits", "classes_info",
                    "attendance_percentage", "midterm_score", "assignment_score", "quiz_score", "subject_average"
                ]].rename(columns={
                    "subject_code": "Code",
                    "subject_name": "Subject Name",
                    "credits": "Credits",
                    "classes_info": "Attended / Total",
                    "attendance_percentage": "Attendance %",
                    "midterm_score": "Midterm Score",
                    "assignment_score": "Assignment %",
                    "quiz_score": "Quiz Score",
                    "subject_average": "Subject Average"
                })

                st.dataframe(df_sub_display, use_container_width=True)

            st.markdown("#### Overall Cumulative Performance")
            ac_c1, ac_c2, ac_c3, ac_c4 = st.columns(4)
            with ac_c1:
                render_metric_card("Overall Avg Attendance", f"{summary['avg_attendance']}%", "Across All Subjects")
            with ac_c2:
                render_metric_card("Midterm Average", f"{summary['avg_midterm']} / 100", "Midterm Exams")
            with ac_c3:
                render_metric_card("Assignment Completion", f"{summary['avg_assignment']}%", "Coursework Marks")
            with ac_c4:
                render_metric_card("Quiz Average", f"{summary['avg_quiz']} / 100", "Continuous Quizzes")

        # TAB 2: SHAP EXPLAINABLE AI
        with tab2:
            st.subheader("Why did the AI predict this outcome?")
            st.info("SHAP (SHapley Additive exPlanations) breaks down exactly how each of your academic factors influenced your score prediction positively or negatively.")

            col_pos, col_neg = st.columns(2)
            with col_pos:
                st.markdown("##### 🟢 Top Positive Boosters")
                for f in shap_explanation.get("top_positive_features", []):
                    feat_name = f["feature"].replace("_", " ").title()
                    st.success(f"**{feat_name}**: Value `{f['value']}` boosted score by **+{f['impact']:.2f} points**")

            with col_neg:
                st.markdown("##### 🔴 Areas Dragging Down Score")
                for f in shap_explanation.get("top_negative_features", []):
                    feat_name = f["feature"].replace("_", " ").title()
                    st.error(f"**{feat_name}**: Value `{f['value']}` reduced score by **{f['impact']:.2f} points**")

            st.markdown("#### Complete SHAP Feature Impact Chart")
            if shap_explanation.get("all_contributions"):
                fig_shap = AcademicCharts.plot_shap_waterfall_bar(shap_explanation["all_contributions"])
                st.plotly_chart(fig_shap, use_container_width=True)

        # TAB 3: PERSONALIZED RECOMMENDATIONS
        with tab3:
            st.subheader("AI-Driven Personalized Academic Action Plan")
            for rec in recommendations:
                category = rec.get("category", "")
                priority = rec.get("priority", "MEDIUM")
                title = rec.get("title", "")
                desc = rec.get("description", "")

                if priority in ["HIGH", "CRITICAL"]:
                    st.error(f"🚨 **[{category.upper()} - {priority} PRIORITY] {title}**\n\n{desc}")
                elif priority == "MEDIUM":
                    st.warning(f"⚠️ **[{category.upper()} - {priority} PRIORITY] {title}**\n\n{desc}")
                else:
                    st.success(f"✅ **[{category.upper()} - {priority} PRIORITY] {title}**\n\n{desc}")

        # TAB 4: RADAR SKILL BREAKDOWN
        with tab4:
            st.subheader("Multi-Dimensional Academic Radar Matrix")
            fig_radar = AcademicCharts.plot_student_performance_radar(student_features)
            st.plotly_chart(fig_radar, use_container_width=True)

        # TAB 5: UPDATE STUDY HABITS & PDF
        with tab5:
            st.subheader("Update Your Study Habits & Download Official Report")

            with st.form("student_habits_form"):
                st.markdown("##### 📝 Self-Reported Study Parameters")
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    new_study = st.slider("Weekly Study Hours", min_value=1.0, max_value=40.0, value=float(student.study_hours_per_week))
                    new_sleep = st.slider("Daily Sleep Hours", min_value=4.0, max_value=12.0, value=float(student.sleep_hours_per_day))
                with col_h2:
                    new_gpa = st.number_input("Previous GPA", min_value=0.0, max_value=4.0, value=float(student.previous_gpa), step=0.1)
                    new_extra = st.checkbox("Participate in Extracurricular Activities", value=student.extracurricular_activities)
                    new_net = st.checkbox("Have Home High-Speed Internet Access", value=student.internet_access)

                save_habits = st.form_submit_button("Update Profile & Recalculate Prediction")

                if save_habits:
                    ok, msg = UserService.update_student_metrics(
                        db=db,
                        student_id=student.id,
                        study_hours=new_study,
                        sleep_hours=new_sleep,
                        previous_gpa=new_gpa,
                        extracurricular=new_extra,
                        internet_access=new_net
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("---")
            st.markdown("##### 📄 Download Official Student Intelligence Report Card")
            if st.button("Generate & Download PDF Report", type="primary"):
                student_dict = {
                    "full_name": user.full_name if user else "N/A",
                    "roll_number": student.roll_number,
                    "department": dept.name if dept else "Computer Science",
                    "semester": student.semester,
                    "study_hours": student.study_hours_per_week,
                    "previous_gpa": student.previous_gpa
                }

                pdf_bytes = PDFReportService.generate_student_pdf_report(
                    student_data=student_dict,
                    academic_data={"subject_breakdown": subject_breakdown},
                    prediction_data=prediction,
                    recommendations=recommendations
                )

                st.download_button(
                    label=f"⬇️ Download PDF Report Card ({student.roll_number})",
                    data=pdf_bytes,
                    file_name=f"Report_Card_{student.roll_number}.pdf",
                    mime="application/pdf"
                )

"""
Teacher Dashboard View.
Provides class analytics, student risk detection, attendance/marks management, and PDF report downloads.
"""

import streamlit as st
import pandas as pd
from database.connection import get_db
from database.models import StudentProfile, Subject, ExamTypeEnum
from services.user_service import UserService
from services.academic_service import AcademicService
from services.report_service import PDFReportService
from ml.predictor import ModelPredictor
from ml.explainer import SHAPExplainer
from ml.recommender import RecommendationEngine
from charts.plotly_charts import AcademicCharts
from frontend.components import render_header, render_metric_card


def render_teacher_dashboard():
    """Render Faculty & Teacher Management Dashboard."""
    render_header("Faculty & Academic Management Hub", "Track Student Attendance, Grade Assessments, and Early Warning Risks")

    predictor = ModelPredictor()
    explainer = SHAPExplainer(predictor)

    with get_db() as db:
        students = UserService.get_all_students(db)
        subjects = AcademicService.get_all_subjects(db)

        if not students:
            st.warning("No student records found in the database. Please add or import students.")
            return

        # Prepare Student Predictions Summary DataFrame dynamically from live academic summary
        rows = []
        for s in students:
            user = s.user
            summary = AcademicService.get_student_academic_summary(db, s.id)

            feats = {
                "attendance_percentage": summary["avg_attendance"],
                "study_hours_per_week": s.study_hours_per_week,
                "previous_gpa": s.previous_gpa,
                "midterm_score": summary["avg_midterm"],
                "assignment_completion": summary["avg_assignment"],
                "quiz_score": summary["avg_quiz"],
                "sleep_hours_per_day": s.sleep_hours_per_day,
                "extracurricular": 1 if s.extracurricular_activities else 0,
                "internet_access": 1 if s.internet_access else 0
            }

            pred = predictor.predict_student(feats)
            rows.append({
                "Student ID": s.id,
                "Roll Number": s.roll_number,
                "Name": user.full_name if user else "N/A",
                "Attendance %": summary["avg_attendance"],
                "Midterm Score": summary["avg_midterm"],
                "Assignment %": summary["avg_assignment"],
                "Quiz Score": summary["avg_quiz"],
                "Predicted Score": pred["predicted_score"],
                "Predicted Grade": pred["predicted_grade"],
                "Risk Level": pred["risk_level"],
                "Pass Prob %": f"{int(pred['pass_probability']*100)}%"
            })

        df_summary = pd.DataFrame(rows)

        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card("Class Total Students", str(len(df_summary)), "Enrolled")
        with c2:
            critical_count = len(df_summary[df_summary["Risk Level"].isin(["HIGH", "CRITICAL"])])
            render_metric_card("At-Risk Students", str(critical_count), "Requires Intervention", delta_color="#EF4444")
        with c3:
            avg_score = round(df_summary["Predicted Score"].mean(), 1)
            render_metric_card("Class Avg Predicted Score", f"{avg_score} / 100", "Overall Class Score")
        with c4:
            avg_att = round(df_summary["Attendance %"].mean(), 1)
            render_metric_card("Class Avg Attendance", f"{avg_att}%", "Overall Attendance")

        st.markdown("---")

        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Class Analytics & Risk Detection",
            "📅 Attendance Management",
            "📝 Marks Management",
            "📄 Generate PDF Academic Reports"
        ])

        # TAB 1: CLASS ANALYTICS & RISK DETECTION
        with tab1:
            st.subheader("Student Risk Flags & Performance Matrix")

            # Risk Filter
            selected_risk = st.multiselect(
                "Filter by Risk Level",
                ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                default=["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            )
            df_filtered = df_summary[df_summary["Risk Level"].isin(selected_risk)]
            st.dataframe(df_filtered, use_container_width=True)

            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                risk_counts = df_summary["Risk Level"].value_counts().to_dict()
                fig_donut = AcademicCharts.plot_risk_distribution_donut(risk_counts)
                st.plotly_chart(fig_donut, use_container_width=True)

            with col_ch2:
                fig_scatter = AcademicCharts.plot_attendance_vs_score_scatter(
                    pd.DataFrame([{
                        "attendance_percentage": r["Attendance %"],
                        "final_score": r["Predicted Score"],
                        "risk_level": r["Risk Level"],
                        "study_hours_per_week": 10,
                        "previous_gpa": 3.0,
                        "midterm_score": r["Midterm Score"]
                    } for r in rows])
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

        # TAB 2: ATTENDANCE MANAGEMENT
        with tab2:
            st.subheader("Record / Update Student Attendance")
            st_map_att = {f"{s.roll_number} - {s.user.full_name if s.user else ''}": s.id for s in students}
            sub_map_att = {f"{sub.subject_code} - {sub.name}": sub.id for sub in subjects} if subjects else {}

            with st.form("attendance_form"):
                if not sub_map_att:
                    st.error("No subjects available in the system.")
                sel_student_label_att = st.selectbox("Select Student *", list(st_map_att.keys()))
                sel_sub_label_att = st.selectbox("Select Subject *", list(sub_map_att.keys())) if sub_map_att else None
                tot_cls = st.number_input("Total Classes Conducted", min_value=1, value=50)
                att_cls = st.number_input("Classes Attended by Student", min_value=0, max_value=int(tot_cls), value=40)
                submit_att = st.form_submit_button("Save Attendance", type="primary")

                if submit_att:
                    if not sel_sub_label_att:
                        st.error("Cannot save attendance: No subject selected.")
                    else:
                        student_id = st_map_att[sel_student_label_att]
                        subject_id = sub_map_att[sel_sub_label_att]
                        ok, msg = AcademicService.update_attendance(db, student_id, subject_id, tot_cls, att_cls)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        # TAB 3: MARKS MANAGEMENT
        with tab3:
            st.subheader("Record / Update Student Assessment Marks")
            st_map_mk = {f"{s.roll_number} - {s.user.full_name if s.user else ''}": s.id for s in students}
            sub_map_mk = {f"{sub.subject_code} - {sub.name}": sub.id for sub in subjects} if subjects else {}

            with st.form("marks_form"):
                if not sub_map_mk:
                    st.error("No subjects available in the system.")
                sel_student_label_mk = st.selectbox("Select Student *", list(st_map_mk.keys()), key="mk_student_sel")
                sel_sub_label_mk = st.selectbox("Select Subject *", list(sub_map_mk.keys()), key="mk_sub_sel") if sub_map_mk else None
                exam_type = st.selectbox("Exam / Assessment Type", [e.value for e in ExamTypeEnum])
                score_val = st.number_input("Score Obtained (0 - 100)", min_value=0.0, max_value=100.0, value=75.0)
                submit_mk = st.form_submit_button("Save Exam Score", type="primary")

                if submit_mk:
                    if not sel_sub_label_mk:
                        st.error("Cannot save marks: No subject selected.")
                    else:
                        student_id = st_map_mk[sel_student_label_mk]
                        subject_id = sub_map_mk[sel_sub_label_mk]
                        ok, msg = AcademicService.record_marks(db, student_id, subject_id, ExamTypeEnum(exam_type), score_val)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        # TAB 4: PDF REPORT GENERATION
        with tab4:
            st.subheader("Generate Official PDF Student Report Card")
            st_map_pdf = {f"{s.roll_number} - {s.user.full_name if s.user else ''}": s.id for s in students}
            sel_student_label_pdf = st.selectbox("Select Student for PDF Generation", list(st_map_pdf.keys()), key="pdf_student_sel")

            if st.button("📄 Generate & Download PDF Report", type="primary"):
                sel_student_id = st_map_pdf[sel_student_label_pdf]
                sel_student_pdf = next((s for s in students if s.id == sel_student_id), None)

                if sel_student_pdf:
                    user = sel_student_pdf.user
                    dept = sel_student_pdf.department
                    summary = AcademicService.get_student_academic_summary(db, sel_student_pdf.id)

                    student_dict = {
                        "full_name": user.full_name if user else "N/A",
                        "roll_number": sel_student_pdf.roll_number,
                        "department": dept.name if dept else "Computer Science",
                        "semester": sel_student_pdf.semester,
                        "study_hours": sel_student_pdf.study_hours_per_week,
                        "previous_gpa": sel_student_pdf.previous_gpa
                    }

                    feats = {
                        "attendance_percentage": summary["avg_attendance"],
                        "study_hours_per_week": sel_student_pdf.study_hours_per_week,
                        "previous_gpa": sel_student_pdf.previous_gpa,
                        "midterm_score": summary["avg_midterm"],
                        "assignment_completion": summary["avg_assignment"],
                        "quiz_score": summary["avg_quiz"],
                        "sleep_hours_per_day": sel_student_pdf.sleep_hours_per_day,
                        "extracurricular": 1 if sel_student_pdf.extracurricular_activities else 0,
                        "internet_access": 1 if sel_student_pdf.internet_access else 0
                    }

                    pred_res = predictor.predict_student(feats)
                    shap_res = explainer.explain_prediction(feats)
                    recs = RecommendationEngine.generate_recommendations(feats, pred_res, shap_res)

                    sub_breakdown = AcademicService.get_student_subject_breakdown(db, sel_student_pdf.id)

                    pdf_bytes = PDFReportService.generate_student_pdf_report(
                        student_data=student_dict,
                        academic_data={"subject_breakdown": sub_breakdown},
                        prediction_data=pred_res,
                        recommendations=recs
                    )

                    st.download_button(
                        label=f"⬇️ Download Official Report Card ({sel_student_pdf.roll_number})",
                        data=pdf_bytes,
                        file_name=f"Report_Card_{sel_student_pdf.roll_number}.pdf",
                        mime="application/pdf"
                    )

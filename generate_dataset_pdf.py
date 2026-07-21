"""
Script to generate the complete Student Performance Dataset in PDF format using ReportLab.
"""

import io
import os
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from ml.dataset_generator import SyntheticDatasetGenerator
from database.connection import get_db
from services.user_service import UserService
from services.academic_service import AcademicService
from ml.predictor import ModelPredictor


def generate_pdf_dataset(output_path: str = "Student_Performance_Dataset.pdf") -> str:
    """Generate professional multi-page PDF dataset report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(letter),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    styles = getSampleStyleSheet()

    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        alignment=0
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2563EB")
    )
    h2_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=5
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155")
    )
    th_style = ParagraphStyle(
        "THStyle",
        parent=body_style,
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("AI-DRIVEN STUDENT PERFORMANCE PREDICTION PLATFORM", subtitle_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Institutional Student Performance Dataset & Academic Metrics", title_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceAfter=10))

    # Fetch Data: Try database records first, supplement with generated samples
    rows = []
    predictor = ModelPredictor()

    with get_db() as db:
        students = UserService.get_all_students(db)
        for s in students:
            user = s.user
            dept = s.department
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
                "Roll No": s.roll_number,
                "Name": user.full_name if user else "N/A",
                "Dept": dept.code if dept else "CS",
                "Att. %": f"{summary['avg_attendance']}%",
                "Study Hrs": f"{s.study_hours_per_week}h",
                "Prev GPA": f"{s.previous_gpa}",
                "Midterm": summary["avg_midterm"],
                "Assign.": f"{summary['avg_assignment']}%",
                "Quiz": summary["avg_quiz"],
                "Score": pred["predicted_score"],
                "GPA": pred["predicted_gpa"],
                "Grade": pred["predicted_grade"],
                "Risk": pred["risk_level"]
            })

    # If DB has fewer than 25 records, generate synthetic cohort rows for dataset report completeness
    if len(rows) < 30:
        df_syn = SyntheticDatasetGenerator.generate_dataset(num_samples=40, seed=42)
        for idx, r in df_syn.iterrows():
            rows.append({
                "Roll No": f"CS-2024-{(idx+1):03d}",
                "Name": f"Student {(idx+1):03d}",
                "Dept": "CS",
                "Att. %": f"{r['attendance_percentage']}%",
                "Study Hrs": f"{r['study_hours_per_week']}h",
                "Prev GPA": f"{r['previous_gpa']}",
                "Midterm": r["midterm_score"],
                "Assign.": f"{r['assignment_completion']}%",
                "Quiz": r["quiz_score"],
                "Score": r["final_score"],
                "GPA": r["final_gpa"],
                "Grade": r["grade"],
                "Risk": r["risk_level"]
            })

    # Summary Statistics Banner Table
    st_df = pd.DataFrame(rows)
    total_records = len(st_df)
    critical_count = len(st_df[st_df["Risk"].isin(["HIGH", "CRITICAL"])])
    avg_score = round(pd.to_numeric(st_df["Score"]).mean(), 1) if "Score" in st_df else 75.0

    kpi_data = [
        [
            Paragraph(f"<b>Total Dataset Records:</b> {total_records}", body_style),
            Paragraph(f"<b>Avg Score:</b> {avg_score} / 100", body_style),
            Paragraph(f"<b>At-Risk Students:</b> {critical_count}", body_style),
            Paragraph("<b>Target Variable:</b> Final Performance Score", body_style)
        ]
    ]
    t_kpi = Table(kpi_data, colWidths=[180, 180, 180, 200])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 10))

    # 2. Main Dataset Table
    story.append(Paragraph("Complete Student Performance Dataset Records", h2_style))

    table_data = [[
        Paragraph("Roll No", th_style),
        Paragraph("Full Name", th_style),
        Paragraph("Dept", th_style),
        Paragraph("Att %", th_style),
        Paragraph("Study Hrs", th_style),
        Paragraph("Prev GPA", th_style),
        Paragraph("Midterm", th_style),
        Paragraph("Assign", th_style),
        Paragraph("Quiz", th_style),
        Paragraph("Score", th_style),
        Paragraph("GPA", th_style),
        Paragraph("Grade", th_style),
        Paragraph("Risk Level", th_style)
    ]]

    for r in rows:
        risk_color = "#22C55E" if r["Risk"] == "LOW" else "#F59E0B" if r["Risk"] == "MEDIUM" else "#EF4444"
        table_data.append([
            Paragraph(f"<b>{r['Roll No']}</b>", body_style),
            Paragraph(r["Name"], body_style),
            Paragraph(r["Dept"], body_style),
            Paragraph(str(r["Att. %"]), body_style),
            Paragraph(str(r["Study Hrs"]), body_style),
            Paragraph(str(r["Prev GPA"]), body_style),
            Paragraph(str(r["Midterm"]), body_style),
            Paragraph(str(r["Assign."]), body_style),
            Paragraph(str(r["Quiz"]), body_style),
            Paragraph(f"<b>{r['Score']}</b>", body_style),
            Paragraph(f"<b>{r['GPA']}</b>", body_style),
            Paragraph(f"<b>{r['Grade']}</b>", body_style),
            Paragraph(f"<font color='{risk_color}'><b>{r['Risk']}</b></font>", body_style)
        ])

    # Col Widths total = 742 (Landscape letter width - margins = 792 - 50 = 742)
    t_dataset = Table(table_data, colWidths=[70, 95, 40, 50, 55, 50, 50, 50, 45, 50, 40, 45, 102])
    t_dataset.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))
    story.append(t_dataset)

    # Footer
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=5))
    story.append(Paragraph("Generated by AI-Driven Academic Intelligence Platform • Institutional Official PDF Dataset Export", subtitle_style))

    doc.build(story)
    print(f"PDF Dataset generated successfully at: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_pdf_dataset()

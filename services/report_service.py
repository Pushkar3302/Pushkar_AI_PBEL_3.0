"""
ReportLab PDF Generation Service.
Generates institutional student academic report cards and AI prediction reports in PDF format.
"""

import io
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class PDFReportService:
    """Service to create PDF Academic Intelligence Report Cards."""

    @staticmethod
    def generate_student_pdf_report(
        student_data: Dict[str, Any],
        academic_data: Dict[str, Any],
        prediction_data: Dict[str, Any],
        recommendations: List[Dict[str, str]]
    ) -> bytes:
        """Generate PDF report card as bytes buffer."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Paragraph Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1E293B"),
            alignment=0
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#64748B")
        )
        h2_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "BodyTextCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#334155")
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("ACADEMIC INTELLIGENCE PLATFORM", subtitle_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph("Student Performance & AI Prediction Report", title_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3B82F6"), spaceAfter=15))

        # 2. Student Profile Table
        story.append(Paragraph("Student Profile", h2_style))
        profile_table_data = [
            [
                Paragraph(f"<b>Name:</b> {student_data.get('full_name', 'N/A')}", body_style),
                Paragraph(f"<b>Roll Number:</b> {student_data.get('roll_number', 'N/A')}", body_style)
            ],
            [
                Paragraph(f"<b>Department:</b> {student_data.get('department', 'N/A')}", body_style),
                Paragraph(f"<b>Semester:</b> {student_data.get('semester', '1')}", body_style)
            ],
            [
                Paragraph(f"<b>Study Hours/Wk:</b> {student_data.get('study_hours', '10')}", body_style),
                Paragraph(f"<b>Previous GPA:</b> {student_data.get('previous_gpa', '3.0')}", body_style)
            ]
        ]
        t_profile = Table(profile_table_data, colWidths=[270, 270])
        t_profile.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_profile)
        story.append(Spacer(1, 15))

        # 3. Subject-by-Subject Academic Breakdown Table
        subject_breakdown = academic_data.get("subject_breakdown", [])
        if subject_breakdown:
            story.append(Paragraph("Individual Subject Attendance & Marks Breakdown", h2_style))
            th_style = ParagraphStyle("TH_Sub", parent=body_style, fontName="Helvetica-Bold", textColor=colors.white, fontSize=9)
            td_style = ParagraphStyle("TD_Sub", parent=body_style, fontSize=9)

            sub_table_data = [
                [
                    Paragraph("Code", th_style),
                    Paragraph("Subject Name", th_style),
                    Paragraph("Att. %", th_style),
                    Paragraph("Midterm", th_style),
                    Paragraph("Assign.", th_style),
                    Paragraph("Quiz", th_style),
                    Paragraph("Average", th_style)
                ]
            ]

            for s_item in subject_breakdown:
                sub_table_data.append([
                    Paragraph(f"<b>{s_item.get('subject_code', '')}</b>", td_style),
                    Paragraph(s_item.get('subject_name', ''), td_style),
                    Paragraph(f"{s_item.get('attendance_percentage', 0.0)}%", td_style),
                    Paragraph(f"{s_item.get('midterm_score', 0.0)}", td_style),
                    Paragraph(f"{s_item.get('assignment_score', 0.0)}", td_style),
                    Paragraph(f"{s_item.get('quiz_score', 0.0)}", td_style),
                    Paragraph(f"<b>{s_item.get('subject_average', 0.0)}</b>", td_style)
                ])

            t_sub = Table(sub_table_data, colWidths=[55, 175, 55, 60, 60, 55, 60])
            t_sub.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
            ]))
            story.append(t_sub)
            story.append(Spacer(1, 15))

        # 4. AI Prediction Summary Table
        story.append(Paragraph("AI Performance Prediction & Risk Assessment", h2_style))
        risk = prediction_data.get("risk_level", "LOW")
        risk_color = "#22C55E" if risk == "LOW" else "#F59E0B" if risk == "MEDIUM" else "#EF4444"

        pred_table_data = [
            [
                Paragraph("Metric", ParagraphStyle("TH", parent=body_style, fontName="Helvetica-Bold", textColor=colors.white)),
                Paragraph("Predicted Value", ParagraphStyle("TH", parent=body_style, fontName="Helvetica-Bold", textColor=colors.white))
            ],
            [Paragraph("Predicted Final Score", body_style), Paragraph(f"<b>{prediction_data.get('predicted_score', 0.0)} / 100</b>", body_style)],
            [Paragraph("Predicted GPA", body_style), Paragraph(f"<b>{prediction_data.get('predicted_gpa', 0.0)} / 4.0</b>", body_style)],
            [Paragraph("Predicted Grade", body_style), Paragraph(f"<b>{prediction_data.get('predicted_grade', 'N/A')}</b>", body_style)],
            [Paragraph("Pass Probability", body_style), Paragraph(f"<b>{int(prediction_data.get('pass_probability', 0.9)*100)}%</b>", body_style)],
            [Paragraph("Academic Risk Level", body_style), Paragraph(f"<font color='{risk_color}'><b>{risk}</b></font>", body_style)],
            [Paragraph("AI Model Confidence", body_style), Paragraph(f"<b>{int(prediction_data.get('confidence_score', 0.9)*100)}%</b> ({prediction_data.get('model_used', 'XGBoost')})", body_style)]
        ]

        t_pred = Table(pred_table_data, colWidths=[270, 270])
        t_pred.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
        ]))
        story.append(t_pred)
        story.append(Spacer(1, 15))

        # 5. Actionable AI Recommendations
        story.append(Paragraph("Personalized Academic Recommendations", h2_style))
        for idx, rec in enumerate(recommendations, 1):
            title = rec.get("title", "")
            desc = rec.get("description", "")
            prio = rec.get("priority", "MEDIUM")
            prio_color = "#EF4444" if prio in ["HIGH", "CRITICAL"] else "#F59E0B" if prio == "MEDIUM" else "#3B82F6"

            item_text = f"<b>{idx}. {title}</b> [<font color='{prio_color}'><b>{prio} PRIORITY</b></font>]<br/>{desc}"
            story.append(Paragraph(item_text, body_style))
            story.append(Spacer(1, 6))

        # 6. Footer Signature Line
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
        story.append(Paragraph("Generated by AI-Driven Academic Intelligence Platform • Institutional Confidential Report", subtitle_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

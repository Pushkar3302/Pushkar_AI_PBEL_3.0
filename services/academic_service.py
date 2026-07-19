"""
Academic Service Module.
Manages Subjects, Semesters, Attendance records, Exam Marks, and Grade updates.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session

from database.models import (
    Department, Subject, Semester, Attendance, Marks, StudentProfile, Prediction, RiskLevelEnum, ExamTypeEnum
)

logger = logging.getLogger(__name__)


class AcademicService:
    """Academic administration service."""

    @staticmethod
    def get_departments(db: Session) -> List[Department]:
        """Fetch all academic departments."""
        return db.query(Department).all()

    @staticmethod
    def create_department(db: Session, name: str, code: str) -> Tuple[bool, str]:
        """Create a new academic department."""
        try:
            code_upper = code.strip().upper()
            existing = db.query(Department).filter_by(code=code_upper).first()
            if existing:
                return False, f"Department code '{code_upper}' already exists."

            dept = Department(name=name.strip(), code=code_upper)
            db.add(dept)
            db.commit()
            return True, f"Department '{name}' ({code_upper}) created successfully!"
        except Exception as e:
            db.rollback()
            return False, f"Failed to create department: {str(e)}"

    @staticmethod
    def create_subject(
        db: Session, code: str, name: str, dept_id: int, credits: int = 3, semester: int = 1
    ) -> Tuple[bool, str]:
        """Create a new subject."""
        try:
            existing = db.query(Subject).filter_by(subject_code=code.upper()).first()
            if existing:
                return False, f"Subject code {code} already exists."

            subject = Subject(
                subject_code=code.upper(),
                name=name.strip(),
                department_id=dept_id,
                credits=credits,
                semester=semester
            )
            db.add(subject)
            db.commit()
            return True, f"Subject '{name}' created successfully!"
        except Exception as e:
            db.rollback()
            return False, f"Error creating subject: {str(e)}"

    @staticmethod
    def get_all_subjects(db: Session) -> List[Subject]:
        """Fetch all subjects; auto-seeds default subjects if empty."""
        subs = db.query(Subject).all()
        if not subs:
            dept = db.query(Department).first()
            if not dept:
                dept = Department(name="Computer Science & Engineering", code="CS")
                db.add(dept)
                db.flush()
            default_subjects = [
                ("CS101", "Data Structures & Algorithms", 4, 1),
                ("CS102", "Database Management Systems", 4, 2),
                ("CS103", "Machine Learning & AI", 4, 3),
                ("CS104", "Computer Networks & Security", 3, 4)
            ]
            for code, name, cred, sem in default_subjects:
                sub = Subject(subject_code=code, name=name, department_id=dept.id, credits=cred, semester=sem)
                db.add(sub)
            db.commit()
            subs = db.query(Subject).all()
        return subs

    @staticmethod
    def update_attendance(
        db: Session, student_id: int, subject_id: int, total_classes: int, attended_classes: int
    ) -> Tuple[bool, str]:
        """Record or update attendance for a student in a subject and recalculate AI prediction."""
        try:
            att_pct = round((attended_classes / max(1, total_classes)) * 100.0, 1)
            record = db.query(Attendance).filter_by(student_id=student_id, subject_id=subject_id).first()

            if record:
                record.total_classes = total_classes
                record.attended_classes = attended_classes
                record.attendance_percentage = att_pct
            else:
                record = Attendance(
                    student_id=student_id,
                    subject_id=subject_id,
                    total_classes=total_classes,
                    attended_classes=attended_classes,
                    attendance_percentage=att_pct
                )
                db.add(record)

            db.commit()

            # Recalculate AI performance prediction dynamically
            AcademicService.recalculate_and_save_prediction(db, student_id)
            return True, f"Attendance ({att_pct}%) recorded and AI prediction updated successfully!"
        except Exception as e:
            db.rollback()
            return False, f"Failed to update attendance: {str(e)}"

    @staticmethod
    def record_marks(
        db: Session,
        student_id: int,
        subject_id: int,
        exam_type: ExamTypeEnum,
        score: float,
        max_score: float = 100.0
    ) -> Tuple[bool, str]:
        """Record or update exam marks for a student and recalculate AI prediction."""
        try:
            record = db.query(Marks).filter_by(
                student_id=student_id, subject_id=subject_id, exam_type=exam_type
            ).first()

            if record:
                record.score_obtained = score
                record.max_score = max_score
            else:
                record = Marks(
                    student_id=student_id,
                    subject_id=subject_id,
                    exam_type=exam_type,
                    score_obtained=score,
                    max_score=max_score
                )
                db.add(record)

            db.commit()

            # Recalculate AI performance prediction dynamically
            AcademicService.recalculate_and_save_prediction(db, student_id)
            return True, f"{exam_type.value} score ({score}/100) recorded and AI prediction updated successfully!"
        except Exception as e:
            db.rollback()
            return False, f"Failed to record marks: {str(e)}"

    @staticmethod
    def get_student_academic_summary(db: Session, student_id: int) -> Dict[str, Any]:
        """Compute aggregated attendance % and average marks for a student."""
        att_records = db.query(Attendance).filter_by(student_id=student_id).all()
        marks_records = db.query(Marks).filter_by(student_id=student_id).all()

        avg_attendance = (
            sum(a.attendance_percentage for a in att_records) / len(att_records)
            if att_records else 75.0
        )

        midterm_scores = [m.score_obtained for m in marks_records if m.exam_type == ExamTypeEnum.MID_TERM]
        assignment_scores = [m.score_obtained for m in marks_records if m.exam_type == ExamTypeEnum.ASSIGNMENT]
        quiz_scores = [m.score_obtained for m in marks_records if m.exam_type == ExamTypeEnum.QUIZ]

        avg_midterm = sum(midterm_scores) / len(midterm_scores) if midterm_scores else 70.0
        avg_assignment = sum(assignment_scores) / len(assignment_scores) if assignment_scores else 80.0
        avg_quiz = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 72.0

        return {
            "avg_attendance": round(avg_attendance, 1),
            "avg_midterm": round(avg_midterm, 1),
            "avg_assignment": round(avg_assignment, 1),
            "avg_quiz": round(avg_quiz, 1)
        }

    @staticmethod
    def get_student_subject_breakdown(db: Session, student_id: int) -> List[Dict[str, Any]]:
        """Fetch subject-by-subject breakdown of attendance and exam marks for a student."""
        subjects = AcademicService.get_all_subjects(db)
        att_records = {a.subject_id: a for a in db.query(Attendance).filter_by(student_id=student_id).all()}
        marks_records = db.query(Marks).filter_by(student_id=student_id).all()

        # Group marks by subject_id and exam_type
        marks_map = {}
        for m in marks_records:
            if m.subject_id not in marks_map:
                marks_map[m.subject_id] = {}
            marks_map[m.subject_id][m.exam_type] = m.score_obtained

        breakdown = []
        for sub in subjects:
            att = att_records.get(sub.id)
            att_pct = att.attendance_percentage if att else 80.0
            classes_info = f"{att.attended_classes}/{att.total_classes}" if att else "N/A"

            sub_marks = marks_map.get(sub.id, {})
            midterm = sub_marks.get(ExamTypeEnum.MID_TERM, 75.0)
            assignment = sub_marks.get(ExamTypeEnum.ASSIGNMENT, 82.0)
            quiz = sub_marks.get(ExamTypeEnum.QUIZ, 78.0)

            subject_avg = round(0.4 * midterm + 0.3 * assignment + 0.3 * quiz, 1)

            breakdown.append({
                "subject_code": sub.subject_code,
                "subject_name": sub.name,
                "credits": sub.credits,
                "semester": sub.semester,
                "classes_info": classes_info,
                "attendance_percentage": att_pct,
                "midterm_score": midterm,
                "assignment_score": assignment,
                "quiz_score": quiz,
                "subject_average": subject_avg
            })

        return breakdown

    @staticmethod
    def recalculate_and_save_prediction(db: Session, student_id: int) -> None:
        """Recalculate AI performance prediction and persist in predictions table."""
        try:
            from ml.predictor import ModelPredictor

            student = db.query(StudentProfile).filter_by(id=student_id).first()
            if not student:
                return

            summary = AcademicService.get_student_academic_summary(db, student_id)
            feats = {
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
            pred_res = predictor.predict_student(feats)

            pred_rec = db.query(Prediction).filter_by(student_id=student_id).order_by(Prediction.created_at.desc()).first()
            if not pred_rec:
                pred_rec = Prediction(
                    student_id=student_id,
                    predicted_score=pred_res["predicted_score"],
                    predicted_gpa=pred_res["predicted_gpa"],
                    predicted_grade=pred_res["predicted_grade"],
                    pass_probability=pred_res["pass_probability"],
                    risk_level=RiskLevelEnum(pred_res["risk_level"]),
                    confidence_score=pred_res["confidence_score"],
                    model_used=pred_res["model_used"]
                )
                db.add(pred_rec)
            else:
                pred_rec.predicted_score = pred_res["predicted_score"]
                pred_rec.predicted_gpa = pred_res["predicted_gpa"]
                pred_rec.predicted_grade = pred_res["predicted_grade"]
                pred_rec.pass_probability = pred_res["pass_probability"]
                pred_rec.risk_level = RiskLevelEnum(pred_res["risk_level"])
                pred_rec.confidence_score = pred_res["confidence_score"]
                pred_rec.model_used = pred_res["model_used"]

            db.commit()
        except Exception as e:
            logger.error(f"Failed to recalculate prediction: {e}")

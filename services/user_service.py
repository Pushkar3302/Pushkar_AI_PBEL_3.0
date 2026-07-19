"""
User Service Module.
Handles User, Student, and Teacher profile queries, updates, and listings.
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload

from database.models import User, StudentProfile, TeacherProfile, Department, Role, RoleEnum, AuditLog, Notification
from authentication.auth_service import AuthService


class UserService:
    """Service class for user administration and profile updates."""

    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        """Fetch all system users with role eager loaded."""
        return db.query(User).options(joinedload(User.role)).all()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Fetch user by ID."""
        return db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()

    @staticmethod
    def get_student_profile(db: Session, user_id: int) -> Optional[StudentProfile]:
        """Fetch student profile by user ID with eager loading."""
        return db.query(StudentProfile).options(
            joinedload(StudentProfile.user),
            joinedload(StudentProfile.department),
            joinedload(StudentProfile.attendance_records),
            joinedload(StudentProfile.marks_records)
        ).filter(StudentProfile.user_id == user_id).first()

    @staticmethod
    def get_all_students(db: Session) -> List[StudentProfile]:
        """Fetch all student profiles with user and department info eagerly loaded."""
        return db.query(StudentProfile).options(
            joinedload(StudentProfile.user),
            joinedload(StudentProfile.department),
            joinedload(StudentProfile.attendance_records),
            joinedload(StudentProfile.marks_records)
        ).all()

    @staticmethod
    def get_all_teachers(db: Session) -> List[TeacherProfile]:
        """Fetch all teacher profiles eagerly loaded."""
        return db.query(TeacherProfile).options(
            joinedload(TeacherProfile.user),
            joinedload(TeacherProfile.department)
        ).all()

    @staticmethod
    def update_student_metrics(
        db: Session,
        student_id: int,
        study_hours: float,
        sleep_hours: float,
        previous_gpa: float,
        extracurricular: bool,
        internet_access: bool
    ) -> Tuple[bool, str]:
        """Update student demographic and academic study habits."""
        try:
            student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
            if not student:
                return False, "Student record not found."

            student.study_hours_per_week = study_hours
            student.sleep_hours_per_day = sleep_hours
            student.previous_gpa = previous_gpa
            student.extracurricular_activities = extracurricular
            student.internet_access = internet_access

            db.commit()
            return True, "Student parameters updated successfully."
        except Exception as e:
            db.rollback()
            return False, f"Failed to update student: {str(e)}"

    @staticmethod
    def update_full_student_profile(
        db: Session,
        student_id: int,
        full_name: str,
        email: str,
        roll_number: str,
        department_id: int,
        semester: int,
        study_hours: float,
        sleep_hours: float,
        previous_gpa: float,
        is_active: bool
    ) -> Tuple[bool, str]:
        """Update complete student account and profile record."""
        try:
            student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
            if not student:
                return False, "Student record not found."

            user = student.user
            if user:
                user.full_name = full_name.strip()
                user.email = email.strip().lower()
                user.is_active = is_active

            student.roll_number = roll_number.strip()
            student.department_id = department_id
            student.semester = semester
            student.study_hours_per_week = study_hours
            student.sleep_hours_per_day = sleep_hours
            student.previous_gpa = previous_gpa

            db.commit()
            return True, f"Student '{full_name}' profile updated successfully."
        except Exception as e:
            db.rollback()
            return False, f"Failed to update student: {str(e)}"

    @staticmethod
    def update_full_teacher_profile(
        db: Session,
        teacher_id: int,
        full_name: str,
        email: str,
        employee_id: str,
        department_id: int,
        designation: str,
        is_active: bool
    ) -> Tuple[bool, str]:
        """Update complete faculty account and profile record."""
        try:
            teacher = db.query(TeacherProfile).filter(TeacherProfile.id == teacher_id).first()
            if not teacher:
                return False, "Teacher record not found."

            user = teacher.user
            if user:
                user.full_name = full_name.strip()
                user.email = email.strip().lower()
                user.is_active = is_active

            teacher.employee_id = employee_id.strip()
            teacher.department_id = department_id
            teacher.designation = designation.strip()

            db.commit()
            return True, f"Faculty '{full_name}' profile updated successfully."
        except Exception as e:
            db.rollback()
            return False, f"Failed to update teacher: {str(e)}"

    @staticmethod
    def toggle_user_active(db: Session, user_id: int) -> Tuple[bool, str]:
        """Enable or disable user account."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found."
            user.is_active = not user.is_active
            db.commit()
            status = "activated" if user.is_active else "deactivated"
            return True, f"User account successfully {status}."
        except Exception as e:
            db.rollback()
            return False, f"Error toggling active status: {str(e)}"

    @staticmethod
    def delete_user(db: Session, user_id: int) -> Tuple[bool, str]:
        """Delete user account and all child profile relationships."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found."
            name = user.full_name

            # Delete child profiles if present
            if user.student_profile:
                db.delete(user.student_profile)
            if user.teacher_profile:
                db.delete(user.teacher_profile)

            # Delete audit logs and notifications for this user
            db.query(AuditLog).filter_by(user_id=user_id).delete(synchronize_session=False)
            db.query(Notification).filter_by(user_id=user_id).delete(synchronize_session=False)

            db.delete(user)
            db.commit()
            return True, f"User '{name}' (ID: {user_id}) deleted successfully."
        except Exception as e:
            db.rollback()
            return False, f"Error deleting user: {str(e)}"

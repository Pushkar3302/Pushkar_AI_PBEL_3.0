"""
SQLAlchemy ORM Database Models for Student Performance Platform.
Normalized schema (3NF) with strict Foreign Keys, indexes, and relationships.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class RoleEnum(str, PyEnum):
    """User Roles."""
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class RiskLevelEnum(str, PyEnum):
    """Student Academic Risk Levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExamTypeEnum(str, PyEnum):
    """Assessment Types."""
    MID_TERM = "MID_TERM"
    END_TERM = "END_TERM"
    ASSIGNMENT = "ASSIGNMENT"
    QUIZ = "QUIZ"


class Role(Base):
    """System User Role Table."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")


class Department(Base):
    """Academic Department Table."""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)

    students = relationship("StudentProfile", back_populates="department")
    teachers = relationship("TeacherProfile", back_populates="department")
    subjects = relationship("Subject", back_populates="department")


class User(Base):
    """System User Account Table."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    role = relationship("Role", back_populates="users")
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class StudentProfile(Base):
    """Student Demographics & Profile Table."""
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    roll_number = Column(String(50), unique=True, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    semester = Column(Integer, default=1, nullable=False)
    gender = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    study_hours_per_week = Column(Float, default=10.0, nullable=False)
    sleep_hours_per_day = Column(Float, default=7.0, nullable=False)
    previous_gpa = Column(Float, default=3.0, nullable=False)
    extracurricular_activities = Column(Boolean, default=False, nullable=False)
    internet_access = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="student_profile")
    department = relationship("Department", back_populates="students")
    attendance_records = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    marks_records = relationship("Marks", back_populates="student", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="student", cascade="all, delete-orphan")


class TeacherProfile(Base):
    """Faculty Profile Table."""
    __tablename__ = "teacher_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    designation = Column(String(100), default="Assistant Professor", nullable=False)

    user = relationship("User", back_populates="teacher_profile")
    department = relationship("Department", back_populates="teachers")


class Semester(Base):
    """Academic Semester Table."""
    __tablename__ = "semesters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    academic_year = Column(String(20), nullable=False)
    is_current = Column(Boolean, default=False, nullable=False)


class Subject(Base):
    """Course / Subject Table."""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    subject_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    credits = Column(Integer, default=3, nullable=False)
    semester = Column(Integer, default=1, nullable=False)

    department = relationship("Department", back_populates="subjects")
    attendance_records = relationship("Attendance", back_populates="subject")
    marks_records = relationship("Marks", back_populates="subject")


class Attendance(Base):
    """Student Subject Attendance Table."""
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    total_classes = Column(Integer, default=50, nullable=False)
    attended_classes = Column(Integer, default=40, nullable=False)
    attendance_percentage = Column(Float, default=80.0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="attendance_records")
    subject = relationship("Subject", back_populates="attendance_records")

    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", name="uq_student_subject_attendance"),
    )


class Marks(Base):
    """Student Marks & Exam Records Table."""
    __tablename__ = "marks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    exam_type = Column(Enum(ExamTypeEnum), nullable=False)
    score_obtained = Column(Float, nullable=False)
    max_score = Column(Float, default=100.0, nullable=False)
    weightage = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="marks_records")
    subject = relationship("Subject", back_populates="marks_records")


class Prediction(Base):
    """AI Student Performance Predictions & SHAP Records."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    predicted_score = Column(Float, nullable=False)
    predicted_gpa = Column(Float, nullable=False)
    predicted_grade = Column(String(10), nullable=False)
    pass_probability = Column(Float, nullable=False)
    risk_level = Column(Enum(RiskLevelEnum), default=RiskLevelEnum.LOW, nullable=False)
    top_shap_features = Column(Text, nullable=True)  # JSON formatted string
    confidence_score = Column(Float, default=0.92, nullable=False)
    model_used = Column(String(50), default="XGBoost Regressor", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("StudentProfile", back_populates="predictions")


class AuditLog(Base):
    """System Operations Audit Log."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")


class Notification(Base):
    """Alerts & Notifications Table."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(20), default="INFO", nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")

"""
Import & Export Service.
Handles CSV Data import with strict Pydantic validation and bulk dataset exporting.
"""

import io
import pandas as pd
from typing import Tuple, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from database.models import User, StudentProfile, Department, Role, RoleEnum
from authentication.auth_service import AuthService


class StudentCSVRow(BaseModel):
    """Pydantic model for validating incoming CSV rows."""
    username: str
    email: str
    full_name: str
    roll_number: str
    department_code: str = "CS"
    study_hours_per_week: float = Field(ge=0, le=70, default=10.0)
    sleep_hours_per_day: float = Field(ge=1, le=16, default=7.0)
    previous_gpa: float = Field(ge=0.0, le=4.0, default=3.0)

    @field_validator("email")
    def validate_email_format(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email format.")
        return v.lower().strip()


class ImportExportService:
    """Service handling bulk CSV import and export of student records."""

    @staticmethod
    def import_students_csv(db: Session, csv_file_bytes: bytes) -> Tuple[int, int, List[str]]:
        """Parse CSV bytes, validate rows using Pydantic, and insert into DB."""
        success_count = 0
        fail_count = 0
        errors = []

        try:
            df = pd.read_csv(io.BytesIO(csv_file_bytes))
            for idx, row in df.iterrows():
                try:
                    row_data = row.to_dict()
                    validated = StudentCSVRow(**row_data)

                    ok, msg, new_user = AuthService.register_user(
                        db=db,
                        username=validated.username,
                        email=validated.email,
                        password="Password@123",  # Default temporary password
                        full_name=validated.full_name,
                        role_name=RoleEnum.STUDENT.value,
                        department_code=validated.department_code,
                        roll_number_or_emp_id=validated.roll_number
                    )

                    if ok and new_user and new_user.student_profile:
                        new_user.student_profile.study_hours_per_week = validated.study_hours_per_week
                        new_user.student_profile.sleep_hours_per_day = validated.sleep_hours_per_day
                        new_user.student_profile.previous_gpa = validated.previous_gpa
                        db.commit()
                        success_count += 1
                    else:
                        fail_count += 1
                        errors.append(f"Row {idx+1} ({validated.username}): {msg}")

                except Exception as ve:
                    fail_count += 1
                    errors.append(f"Row {idx+1}: Validation error - {str(ve)}")

        except Exception as e:
            errors.append(f"Global CSV Parsing error: {str(e)}")

        return success_count, fail_count, errors

    @staticmethod
    def export_students_csv(db: Session) -> str:
        """Export all student profiles as CSV string."""
        students = db.query(StudentProfile).all()
        data = []
        for s in students:
            user = s.user
            dept = s.department
            data.append({
                "Student ID": s.id,
                "Roll Number": s.roll_number,
                "Full Name": user.full_name if user else "",
                "Username": user.username if user else "",
                "Email": user.email if user else "",
                "Department": dept.name if dept else "",
                "Semester": s.semester,
                "Study Hours/Wk": s.study_hours_per_week,
                "Sleep Hours/Day": s.sleep_hours_per_day,
                "Previous GPA": s.previous_gpa
            })

        df = pd.DataFrame(data)
        return df.to_csv(index=False)

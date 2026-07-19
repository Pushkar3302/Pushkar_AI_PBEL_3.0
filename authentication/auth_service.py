"""
Authentication Service handling Password Hashing (bcrypt), User Registration,
Login Validation, Password Reset, and Session Management.
"""

import bcrypt
import logging
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from database.models import User, Role, RoleEnum, StudentProfile, TeacherProfile, Department
from database.connection import get_db

logger = logging.getLogger(__name__)


class AuthService:
    """Service class for user authentication and authorization operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plaintext password using bcrypt."""
        pwd_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a bcrypt hashed password."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @classmethod
    def register_user(
        cls,
        db: Session,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role_name: str,
        department_code: str = "CS",
        roll_number_or_emp_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        """Register a new user with their associated role profile."""
        try:
            # Check existing username or email
            existing_user = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            if existing_user:
                return False, "Username or Email already exists.", None

            # Get Role
            role = db.query(Role).filter_by(name=role_name.upper()).first()
            if not role:
                return False, f"Invalid Role: {role_name}", None

            # Get Department
            dept = db.query(Department).filter_by(code=department_code.upper()).first()
            if not dept:
                dept = db.query(Department).first()
                if not dept:
                    dept = Department(name="Computer Science & Engineering", code="CS")
                    db.add(dept)
                    db.flush()

            # Hash Password
            hashed_pwd = cls.hash_password(password)

            # Create User
            new_user = User(
                username=username.strip(),
                email=email.strip().lower(),
                password_hash=hashed_pwd,
                full_name=full_name.strip(),
                role_id=role.id,
                is_active=True
            )
            db.add(new_user)
            db.flush()

            # Create associated role profile
            identifier = roll_number_or_emp_id or f"ID-{new_user.id:04d}"
            if role.name == RoleEnum.STUDENT.value:
                student_prof = StudentProfile(
                    user_id=new_user.id,
                    roll_number=identifier,
                    department_id=dept.id,
                    semester=1
                )
                db.add(student_prof)
            elif role.name == RoleEnum.TEACHER.value:
                teacher_prof = TeacherProfile(
                    user_id=new_user.id,
                    employee_id=identifier,
                    department_id=dept.id,
                    designation="Assistant Professor"
                )
                db.add(teacher_prof)

            db.commit()
            db.refresh(new_user)
            return True, "User registered successfully!", new_user

        except Exception as e:
            db.rollback()
            logger.error(f"Error registering user: {e}")
            return False, f"Registration failed: {str(e)}", None

    @classmethod
    def authenticate_user(
        cls, db: Session, username_or_email: str, password: str
    ) -> Tuple[bool, str, Optional[User]]:
        """Authenticate user credentials."""
        try:
            user = db.query(User).filter(
                (User.username == username_or_email.strip()) |
                (User.email == username_or_email.strip().lower())
            ).first()

            if not user:
                return False, "Invalid username or password.", None

            if not user.is_active:
                return False, "Account is disabled. Please contact Admin.", None

            if not cls.verify_password(password, user.password_hash):
                return False, "Invalid username or password.", None

            return True, "Login successful!", user

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, f"Authentication error: {str(e)}", None

    @classmethod
    def reset_password(
        cls, db: Session, email: str, new_password: str
    ) -> Tuple[bool, str]:
        """Reset user password by email."""
        try:
            user = db.query(User).filter(User.email == email.strip().lower()).first()
            if not user:
                return False, "No user found with the provided email address."

            user.password_hash = cls.hash_password(new_password)
            db.commit()
            return True, "Password has been updated successfully!"

        except Exception as e:
            db.rollback()
            logger.error(f"Error resetting password: {e}")
            return False, f"Password reset failed: {str(e)}"

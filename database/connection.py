"""
Database Connection Manager using SQLAlchemy.
Supports both MySQL and SQLite database backends seamlessly.
"""

import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.settings import settings
from database.models import Base, Role, User, Department, Subject, StudentProfile, TeacherProfile, RoleEnum

logger = logging.getLogger(__name__)

# Configure SQLAlchemy engine
is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables and seed initial roles, department, and default subjects."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")

        # Seed basic initial data
        session = SessionLocal()
        try:
            # Seed Roles
            roles = ["ADMIN", "TEACHER", "STUDENT"]
            for r_name in roles:
                role = session.query(Role).filter_by(name=r_name).first()
                if not role:
                    role = Role(name=r_name, description=f"{r_name.capitalize()} System Role")
                    session.add(role)

            # Seed Default Department
            dept = session.query(Department).filter_by(code="CS").first()
            if not dept:
                dept = Department(name="Computer Science & Engineering", code="CS")
                session.add(dept)
                session.flush()

            # Seed Default Subjects
            default_subjects = [
                ("CS101", "Data Structures & Algorithms", 4, 1),
                ("CS102", "Database Management Systems", 4, 2),
                ("CS103", "Machine Learning & AI", 4, 3),
                ("CS104", "Computer Networks & Security", 3, 4)
            ]
            for code, name, cred, sem in default_subjects:
                sub = session.query(Subject).filter_by(subject_code=code).first()
                if not sub:
                    sub = Subject(
                        subject_code=code,
                        name=name,
                        department_id=dept.id,
                        credits=cred,
                        semester=sem
                    )
                    session.add(sub)

            session.commit()
        except Exception as se:
            session.rollback()
            logger.error(f"Error seeding database: {se}")
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

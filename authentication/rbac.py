"""
Role-Based Access Control (RBAC) Module.
Defines permissions matrix and helper utilities for checking user privileges.
"""

from typing import List, Dict, Any, Optional
from database.models import RoleEnum


class RBACManager:
    """RBAC Manager enforcing permissions per user role."""

    # Permissions Matrix
    PERMISSIONS: Dict[str, List[str]] = {
        RoleEnum.ADMIN.value: [
            "manage_users",
            "view_all_dashboards",
            "manage_departments",
            "manage_subjects",
            "manage_semesters",
            "view_audit_logs",
            "csv_import_export",
            "run_ai_training",
            "predict_performance",
            "view_all_analytics",
            "download_reports",
            "manage_settings"
        ],
        RoleEnum.TEACHER.value: [
            "view_teacher_dashboard",
            "manage_attendance",
            "manage_marks",
            "view_class_analytics",
            "csv_import_export",
            "predict_performance",
            "download_reports"
        ],
        RoleEnum.STUDENT.value: [
            "view_student_dashboard",
            "view_own_attendance",
            "view_own_marks",
            "view_own_predictions",
            "download_own_report",
            "view_own_recommendations"
        ]
    }

    @classmethod
    def has_permission(cls, role_name: str, permission: str) -> bool:
        """Check if a given role has a specific permission."""
        user_role = role_name.upper() if role_name else ""
        allowed_permissions = cls.PERMISSIONS.get(user_role, [])
        return permission in allowed_permissions

    @classmethod
    def is_admin(cls, role_name: str) -> bool:
        """Return True if user is Admin."""
        return role_name.upper() == RoleEnum.ADMIN.value

    @classmethod
    def is_teacher(cls, role_name: str) -> bool:
        """Return True if user is Teacher."""
        return role_name.upper() == RoleEnum.TEACHER.value

    @classmethod
    def is_student(cls, role_name: str) -> bool:
        """Return True if user is Student."""
        return role_name.upper() == RoleEnum.STUDENT.value


rbac = RBACManager()

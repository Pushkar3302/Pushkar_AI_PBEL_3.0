"""
AI-Driven Student Performance Prediction & Academic Intelligence Platform
Main Streamlit Application Entrypoint.
"""

import streamlit as st

# 1. Configure Page Layout & Title
st.set_page_config(
    page_title="AI Academic Intelligence Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

from database.connection import init_db, get_db
from database.models import RoleEnum
from authentication.auth_service import AuthService
from authentication.rbac import rbac
from services.user_service import UserService
from frontend.components import apply_custom_styles
from frontend.views.auth_view import render_auth_view
from frontend.views.admin_dashboard import render_admin_dashboard
from frontend.views.teacher_dashboard import render_teacher_dashboard
from frontend.views.student_dashboard import render_student_dashboard
from frontend.views.analytics_view import render_analytics_view
from frontend.views.settings_view import render_settings_view

# 2. Session State Initialization
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "Dark"

# Inject Custom Theme Styles
apply_custom_styles(st.session_state["theme_mode"])

# 3. Initialize Database and Seed Default User Accounts
@st.cache_resource
def setup_database():
    init_db()
    with get_db() as db:
        from database.models import User
        # Seed default Admin account if not present
        admin = db.query(User).filter((User.username == "admin") | (User.email == "admin@university.edu")).first()
        if not admin:
            AuthService.register_user(
                db=db,
                username="admin",
                email="admin@university.edu",
                password="AdminPass123",
                full_name="System Administrator",
                role_name=RoleEnum.ADMIN.value,
                department_code="CS"
            )
        elif not admin.is_active:
            admin.is_active = True
            db.commit()

        # Seed default Teacher account
        teacher = db.query(User).filter((User.username == "teacher") | (User.email == "teacher@university.edu")).first()
        if not teacher:
            AuthService.register_user(
                db=db,
                username="teacher",
                email="teacher@university.edu",
                password="TeacherPass123",
                full_name="Dr. Alan Turing",
                role_name=RoleEnum.TEACHER.value,
                department_code="CS",
                roll_number_or_emp_id="EMP-1001"
            )
        elif not teacher.is_active:
            teacher.is_active = True
            db.commit()

        # Seed default Student account
        student = db.query(User).filter((User.username == "student") | (User.email == "student@university.edu")).first()
        if not student:
            AuthService.register_user(
                db=db,
                username="student",
                email="student@university.edu",
                password="StudentPass123",
                full_name="John Doe",
                role_name=RoleEnum.STUDENT.value,
                department_code="CS",
                roll_number_or_emp_id="CS-2024-001"
            )
        elif not student.is_active:
            student.is_active = True
            db.commit()

setup_database()

# Session User Information
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "full_name" not in st.session_state:
    st.session_state["full_name"] = None


def main():
    """Main Application Controller."""

    # Theme Switcher in Sidebar (always accessible)
    st.sidebar.markdown("### 🎨 Appearance")
    theme_choice = st.sidebar.radio(
        "Theme Mode",
        ["🌙 Dark Mode", "☀️ Light Mode"],
        index=0 if st.session_state["theme_mode"] == "Dark" else 1,
        key="app_theme_radio"
    )
    new_theme = "Dark" if "Dark" in theme_choice else "Light"
    if new_theme != st.session_state["theme_mode"]:
        st.session_state["theme_mode"] = new_theme
        st.rerun()

    st.sidebar.markdown("---")

    # If User Not Logged In -> Render Auth View
    if st.session_state["user_id"] is None:
        render_auth_view()
        return

    # User Logged In -> Render Navigation Sidebar
    st.sidebar.markdown("### 🎓 Academic Intelligence")
    st.sidebar.markdown(f"**Logged in as:** `{st.session_state['full_name']}`")
    st.sidebar.markdown(f"**Role:** `{st.session_state['role']}`")
    st.sidebar.markdown("---")

    role = st.session_state["role"]
    nav_options = []

    if rbac.is_admin(role):
        nav_options = ["🏛️ Admin Dashboard", "📊 Institutional Analytics", "⚙️ Settings"]
    elif rbac.is_teacher(role):
        nav_options = ["👨‍🏫 Faculty Dashboard", "📊 Institutional Analytics", "⚙️ Settings"]
    elif rbac.is_student(role):
        nav_options = ["🎓 Student Dashboard", "📊 Analytics Insights", "⚙️ Settings"]
    else:
        nav_options = ["⚙️ Settings"]

    selected_page = st.sidebar.radio("Navigation Menu", nav_options)

    # Logout Button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state["user_id"] = None
        st.session_state["username"] = None
        st.session_state["role"] = None
        st.session_state["full_name"] = None
        st.rerun()

    # Dispatch Selected Page
    if "Admin Dashboard" in selected_page:
        render_admin_dashboard()
    elif "Faculty Dashboard" in selected_page:
        render_teacher_dashboard()
    elif "Student Dashboard" in selected_page:
        render_student_dashboard()
    elif "Analytics" in selected_page or "Insights" in selected_page:
        render_analytics_view()
    elif "Settings" in selected_page:
        render_settings_view()


if __name__ == "__main__":
    main()

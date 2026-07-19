"""
Authentication View (Sign In, Registration, Password Reset).
"""

import streamlit as st
from database.connection import get_db
from database.models import RoleEnum
from authentication.auth_service import AuthService
from services.audit_service import AuditService
from frontend.components import render_header


def render_auth_view():
    """Render Sign In / Registration / Forgot Password UI tabs."""
    render_header("Welcome to Academic Intelligence Platform", "Secure Role-Based Access for Admins, Teachers & Students")

    tab1, tab2, tab3 = st.tabs(["🔑 Sign In / Login", "📝 Student / Teacher Registration", "🔒 Reset Password"])

    # TAB 1: SIGN IN / LOGIN
    with tab1:
        st.subheader("Account Sign In")
        st.info("💡 **Quick Credentials**: Admin (`admin` / `AdminPass123`) • Teacher (`teacher` / `TeacherPass123`) • Student (`student` / `StudentPass123`)")

        with st.form("login_form"):
            username_or_email = st.text_input("Username or Email Address *", placeholder="e.g. admin@university.edu or admin")
            password = st.text_input("Password *", type="password", placeholder="Enter your password")
            
            submit = st.form_submit_button("🔑 Sign In to Platform", type="primary")

            if submit:
                if not username_or_email or not password:
                    st.error("Please fill in all required fields.")
                else:
                    with get_db() as db:
                        ok, msg, user = AuthService.authenticate_user(db, username_or_email, password)
                        if ok and user:
                            st.session_state["user_id"] = user.id
                            st.session_state["username"] = user.username
                            st.session_state["full_name"] = user.full_name
                            st.session_state["role"] = user.role.name

                            AuditService.log_action(db, user.id, "USER_LOGIN", f"User {user.username} logged in successfully.")
                            st.success(f"Welcome back, {user.full_name}!")
                            st.rerun()
                        else:
                            st.error(msg)

    # TAB 2: REGISTER
    with tab2:
        st.subheader("Create New Account")
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                reg_username = st.text_input("Username *")
                reg_email = st.text_input("Institutional Email *")
                reg_password = st.text_input("Password *", type="password")
            with col2:
                reg_fullname = st.text_input("Full Name *")
                reg_role = st.selectbox("Register Role *", [RoleEnum.STUDENT.value, RoleEnum.TEACHER.value])
                reg_id = st.text_input("Roll Number / Employee ID *")

            reg_submit = st.form_submit_button("📝 Register New Account", type="primary")

            if reg_submit:
                if not (reg_username and reg_email and reg_password and reg_fullname):
                    st.error("All required fields must be filled.")
                else:
                    emp_or_roll = reg_id if reg_id else ("ADM-" + reg_username.upper())
                    with get_db() as db:
                        ok, msg, user = AuthService.register_user(
                            db=db,
                            username=reg_username,
                            email=reg_email,
                            password=reg_password,
                            full_name=reg_fullname,
                            role_name=reg_role,
                            department_code="CS",
                            roll_number_or_emp_id=emp_or_roll
                        )
                        if ok:
                            st.success("Account created successfully! Click 'Sign In / Login' tab to log in.")
                        else:
                            st.error(msg)

    # TAB 3: FORGOT PASSWORD
    with tab3:
        st.subheader("Password Recovery")
        with st.form("reset_form"):
            reset_email = st.text_input("Registered Email Address *")
            new_pwd = st.text_input("New Password *", type="password")
            confirm_pwd = st.text_input("Confirm New Password *", type="password")
            reset_submit = st.form_submit_button("🔒 Reset Password", type="primary")

            if reset_submit:
                if new_pwd != confirm_pwd:
                    st.error("Passwords do not match.")
                elif not reset_email or not new_pwd:
                    st.error("All fields are required.")
                else:
                    with get_db() as db:
                        ok, msg = AuthService.reset_password(db, reset_email, new_pwd)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

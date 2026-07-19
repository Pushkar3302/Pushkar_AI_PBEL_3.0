"""
User Settings & Profile Management View.
"""

import streamlit as st
from database.connection import get_db
from database.models import User
from authentication.auth_service import AuthService
from services.user_service import UserService
from frontend.components import render_header


def render_settings_view():
    """Render Account Settings Page."""
    user_id = st.session_state.get("user_id")
    render_header("Account Settings & Security", "Manage your profile, update credentials, and system settings")

    with get_db() as db:
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            st.error("User not found.")
            return

        tab1, tab2 = st.tabs(["👤 Profile Information", "🔑 Change Password"])

        with tab1:
            st.subheader("User Account Details")
            st.text_input("Full Name", value=user.full_name, disabled=True)
            st.text_input("Username", value=user.username, disabled=True)
            st.text_input("Email", value=user.email, disabled=True)
            st.text_input("Role", value=user.role.name if user.role else "N/A", disabled=True)
            st.text_input("Member Since", value=user.created_at.strftime("%Y-%m-%d"), disabled=True)

        with tab2:
            st.subheader("Update Password")
            with st.form("change_pwd_form"):
                curr_pwd = st.text_input("Current Password", type="password")
                new_pwd = st.text_input("New Password", type="password")
                confirm_pwd = st.text_input("Confirm New Password", type="password")
                submit = st.form_submit_button("Update Password")

                if submit:
                    if not AuthService.verify_password(curr_pwd, user.password_hash):
                        st.error("Current password is incorrect.")
                    elif new_pwd != confirm_pwd:
                        st.error("New passwords do not match.")
                    elif len(new_pwd) < 6:
                        st.error("Password must be at least 6 characters long.")
                    else:
                        user.password_hash = AuthService.hash_password(new_pwd)
                        db.commit()
                        st.success("Password updated successfully!")

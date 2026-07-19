"""
Admin Dashboard View.
Provides comprehensive user management (add/view/edit/delete students & teachers),
department & subject setup, CSV import/export, audit logs, and ML model retraining.
"""

import streamlit as st
import pandas as pd
from sqlalchemy.orm import joinedload
from database.connection import get_db
from database.models import User, StudentProfile, TeacherProfile, Department, RoleEnum, AuditLog
from authentication.auth_service import AuthService
from services.user_service import UserService
from services.academic_service import AcademicService
from services.import_export_service import ImportExportService
from services.audit_service import AuditService
from ml.dataset_generator import SyntheticDatasetGenerator
from ml.trainer import ModelTrainer
from charts.plotly_charts import AcademicCharts
from frontend.components import render_header, render_metric_card


def render_admin_dashboard():
    """Render comprehensive Admin Command Center Dashboard."""
    render_header("Institutional Admin Command Center", "Manage Students, Faculty, Departments, System Security & AI Models")

    with get_db() as db:
        students = UserService.get_all_students(db)
        teachers = UserService.get_all_teachers(db)
        users = UserService.get_all_users(db)
        depts = AcademicService.get_departments(db)
        logs = AuditService.get_recent_logs(db, limit=100)

        # KPI Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card("Total Registered Users", str(len(users)), "Active System Accounts")
        with col2:
            render_metric_card("Enrolled Students", str(len(students)), "Active Student Profiles")
        with col3:
            render_metric_card("Faculty Members", str(len(teachers)), "Professors & Instructors")
        with col4:
            render_metric_card("Academic Departments", str(len(depts)), f"{len(depts)} Active Depts")

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👥 All System Users",
        "🎓 Student Directory",
        "👨‍🏫 Faculty Directory",
        "🏛️ Depts & Subjects",
        "📥 CSV Import / Export",
        "🤖 AI Model Retrainer",
        "📜 Audit Logs"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: ALL SYSTEM USERS OVERVIEW
    # --------------------------------------------------------------------------
    with tab1:
        st.subheader("System Account Overview")
        with get_db() as db:
            all_users = UserService.get_all_users(db)
            user_data = [{
                "User ID": u.id,
                "Username": u.username,
                "Email": u.email,
                "Full Name": u.full_name,
                "Role": u.role.name if u.role else "N/A",
                "Is Active": "Yes" if u.is_active else "No",
                "Created At": u.created_at.strftime("%Y-%m-%d %H:%M")
            } for u in all_users]
            st.dataframe(pd.DataFrame(user_data), use_container_width=True)

            st.markdown("---")
            st.markdown("##### ➕ Register New Administrator or System User")
            with st.form("admin_create_user_form"):
                ca1, ca2 = st.columns(2)
                with ca1:
                    new_u_username = st.text_input("Username *", key="adm_new_u_name")
                    new_u_email = st.text_input("Email Address *", key="adm_new_u_email")
                    new_u_password = st.text_input("Password *", type="password", key="adm_new_u_pwd")
                with ca2:
                    new_u_fullname = st.text_input("Full Name *", key="adm_new_u_fname")
                    new_u_role = st.selectbox("Role *", [RoleEnum.ADMIN.value, RoleEnum.TEACHER.value, RoleEnum.STUDENT.value], key="adm_new_u_role")
                    new_u_id = st.text_input("Roll Number / Employee ID (Optional for Admin)", key="adm_new_u_id")

                submit_new_admin_user = st.form_submit_button("➕ Create Account", type="primary")
                if submit_new_admin_user:
                    if not (new_u_username and new_u_email and new_u_password and new_u_fullname):
                        st.error("Username, Email, Password, and Full Name are required.")
                    else:
                        emp_roll = new_u_id if new_u_id else f"ADM-{new_u_username.upper()}"
                        ok, msg, u_obj = AuthService.register_user(
                            db=db,
                            username=new_u_username,
                            email=new_u_email,
                            password=new_u_password,
                            full_name=new_u_fullname,
                            role_name=new_u_role,
                            department_code="CS",
                            roll_number_or_emp_id=emp_roll
                        )
                        if ok:
                            st.success(f"New {new_u_role} account '{new_u_username}' created successfully!")
                            st.rerun()
                        else:
                            st.error(msg)

            st.markdown("---")
            col_act, col_del = st.columns(2)

            with col_act:
                st.markdown("##### ⚙️ Toggle User Active Status")
                uid_toggle = st.number_input("Enter User ID to Toggle", min_value=1, step=1, key="uid_toggle")
                if st.button("Toggle Account Status", key="btn_toggle"):
                    ok, msg = UserService.toggle_user_active(db, int(uid_toggle))
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            with col_del:
                st.markdown("##### 🗑️ Delete User Account")
                uid_delete = st.number_input("Enter User ID to Delete", min_value=1, step=1, key="uid_delete")
                if st.button("Delete Account Permanently", type="secondary", key="btn_del"):
                    ok, msg = UserService.delete_user(db, int(uid_delete))
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    # --------------------------------------------------------------------------
    # TAB 2: STUDENT DIRECTORY & MANAGEMENT
    # --------------------------------------------------------------------------
    with tab2:
        st.subheader("Student Administration & Profile Management")

        st_sub1, st_sub2 = st.tabs(["➕ Add New Student", "🔍 Select & Edit Student Profile"])

        # Sub-tab: Add New Student
        with st_sub1:
            with st.form("add_student_form"):
                st.markdown("##### Fill Student Registration Details")
                c1, c2 = st.columns(2)
                with c1:
                    st_username = st.text_input("Username *", key="new_st_uname")
                    st_email = st.text_input("Email Address *", key="new_st_email")
                    st_password = st.text_input("Password *", type="password", key="new_st_pwd")
                    st_fullname = st.text_input("Full Name *", key="new_st_name")
                    st_roll = st.text_input("Roll Number * (e.g. CS-2024-005)", key="new_st_roll")
                with c2:
                    with get_db() as db:
                        dept_options = {d.code: d for d in AcademicService.get_departments(db)}
                    st_dept_code = st.selectbox("Department *", list(dept_options.keys())) if dept_options else "CS"
                    st_semester = st.number_input("Semester", min_value=1, max_value=8, value=1)
                    st_study = st.number_input("Study Hours/Wk", min_value=0.0, max_value=70.0, value=12.0)
                    st_sleep = st.number_input("Sleep Hours/Day", min_value=1.0, max_value=12.0, value=7.5)
                    st_gpa = st.number_input("Previous GPA", min_value=0.0, max_value=4.0, value=3.2, step=0.1)

                btn_add_st = st.form_submit_button("Register New Student", type="primary")

                if btn_add_st:
                    if not (st_username and st_email and st_password and st_fullname and st_roll):
                        st.error("Please complete all required fields.")
                    else:
                        with get_db() as db:
                            ok, msg, new_user = AuthService.register_user(
                                db=db,
                                username=st_username,
                                email=st_email,
                                password=st_password,
                                full_name=st_fullname,
                                role_name=RoleEnum.STUDENT.value,
                                department_code=st_dept_code,
                                roll_number_or_emp_id=st_roll
                            )
                            if ok and new_user and new_user.student_profile:
                                new_user.student_profile.semester = st_semester
                                new_user.student_profile.study_hours_per_week = st_study
                                new_user.student_profile.sleep_hours_per_day = st_sleep
                                new_user.student_profile.previous_gpa = st_gpa
                                db.commit()
                                st.success(f"Student '{st_fullname}' registered successfully!")
                                st.rerun()
                            else:
                                st.error(msg)

        # Sub-tab: Select & Edit Student
        with st_sub2:
            with get_db() as db:
                all_st = UserService.get_all_students(db)
                if not all_st:
                    st.info("No students found.")
                else:
                    st_map = {
                        f"{s.roll_number} - {s.user.full_name if s.user else 'N/A'} (Dept: {s.department.code if s.department else 'N/A'})": s.id
                        for s in all_st
                    }
                    selected_st_label = st.selectbox("Select Student to View/Edit", list(st_map.keys()))
                    selected_st_id = st_map[selected_st_label]

                    selected_st = db.query(StudentProfile).options(
                        joinedload(StudentProfile.user),
                        joinedload(StudentProfile.department)
                    ).filter(StudentProfile.id == selected_st_id).first()

                    if selected_st:
                        u = selected_st.user
                        d = selected_st.department
                        st.markdown(f"#### Edit Profile: `{selected_st.roll_number}` - {u.full_name if u else ''}")

                        with st.form("edit_student_form"):
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                ed_name = st.text_input("Full Name", value=u.full_name if u else "")
                                ed_email = st.text_input("Email", value=u.email if u else "")
                                ed_roll = st.text_input("Roll Number", value=selected_st.roll_number)
                                ed_active = st.checkbox("Account Active", value=u.is_active if u else True)
                            with ec2:
                                all_depts = AcademicService.get_departments(db)
                                dept_dict = {dept.name: dept.id for dept in all_depts}
                                curr_dept_name = d.name if d else (all_depts[0].name if all_depts else "")
                                ed_dept_name = st.selectbox("Department", list(dept_dict.keys()), index=list(dept_dict.keys()).index(curr_dept_name) if curr_dept_name in dept_dict else 0)
                                ed_sem = st.number_input("Semester", min_value=1, max_value=8, value=int(selected_st.semester))
                                ed_study = st.number_input("Study Hours/Wk", min_value=0.0, max_value=70.0, value=float(selected_st.study_hours_per_week))
                                ed_sleep = st.number_input("Sleep Hours/Day", min_value=1.0, max_value=12.0, value=float(selected_st.sleep_hours_per_day))
                                ed_gpa = st.number_input("Previous GPA", min_value=0.0, max_value=4.0, value=float(selected_st.previous_gpa), step=0.1)

                            btn_save_st = st.form_submit_button("Save Student Changes", type="primary")

                            if btn_save_st:
                                ok, msg = UserService.update_full_student_profile(
                                    db=db,
                                    student_id=selected_st.id,
                                    full_name=ed_name,
                                    email=ed_email,
                                    roll_number=ed_roll,
                                    department_id=dept_dict[ed_dept_name],
                                    semester=ed_sem,
                                    study_hours=ed_study,
                                    sleep_hours=ed_sleep,
                                    previous_gpa=ed_gpa,
                                    is_active=ed_active
                                )
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

    # --------------------------------------------------------------------------
    # TAB 3: FACULTY DIRECTORY & MANAGEMENT
    # --------------------------------------------------------------------------
    with tab3:
        st.subheader("Faculty Administration & Profile Management")

        t_sub1, t_sub2 = st.tabs(["➕ Add New Teacher", "🔍 Select & Edit Faculty Profile"])

        # Sub-tab: Add New Teacher
        with t_sub1:
            with st.form("add_teacher_form"):
                st.markdown("##### Fill Faculty Registration Details")
                tc1, tc2 = st.columns(2)
                with tc1:
                    t_username = st.text_input("Username *", key="new_t_uname")
                    t_email = st.text_input("Email Address *", key="new_t_email")
                    t_password = st.text_input("Password *", type="password", key="new_t_pwd")
                    t_fullname = st.text_input("Full Name *", key="new_t_name")
                with tc2:
                    t_empid = st.text_input("Employee ID * (e.g. EMP-1002)", key="new_t_empid")
                    with get_db() as db:
                        dept_options_t = {d.code: d for d in AcademicService.get_departments(db)}
                    t_dept_code = st.selectbox("Department *", list(dept_options_t.keys()), key="t_dept_code") if dept_options_t else "CS"
                    t_desig = st.selectbox("Designation", ["Assistant Professor", "Associate Professor", "Professor", "Head of Department"])

                btn_add_t = st.form_submit_button("Register New Faculty", type="primary")

                if btn_add_t:
                    if not (t_username and t_email and t_password and t_fullname and t_empid):
                        st.error("Please complete all required fields.")
                    else:
                        with get_db() as db:
                            ok, msg, new_user = AuthService.register_user(
                                db=db,
                                username=t_username,
                                email=t_email,
                                password=t_password,
                                full_name=t_fullname,
                                role_name=RoleEnum.TEACHER.value,
                                department_code=t_dept_code,
                                roll_number_or_emp_id=t_empid
                            )
                            if ok and new_user and new_user.teacher_profile:
                                new_user.teacher_profile.designation = t_desig
                                db.commit()
                                st.success(f"Faculty '{t_fullname}' registered successfully!")
                                st.rerun()
                            else:
                                st.error(msg)

        # Sub-tab: Select & Edit Teacher
        with t_sub2:
            with get_db() as db:
                all_t = UserService.get_all_teachers(db)
                if not all_t:
                    st.info("No faculty profiles found.")
                else:
                    t_map = {
                        f"{t.employee_id} - {t.user.full_name if t.user else 'N/A'} ({t.designation})": t.id
                        for t in all_t
                    }
                    selected_t_label = st.selectbox("Select Faculty to View/Edit", list(t_map.keys()))
                    selected_t_id = t_map[selected_t_label]

                    selected_t = db.query(TeacherProfile).options(
                        joinedload(TeacherProfile.user),
                        joinedload(TeacherProfile.department)
                    ).filter(TeacherProfile.id == selected_t_id).first()

                    if selected_t:
                        tu = selected_t.user
                        td = selected_t.department
                        st.markdown(f"#### Edit Profile: `{selected_t.employee_id}` - {tu.full_name if tu else ''}")

                        with st.form("edit_teacher_form"):
                            etc1, etc2 = st.columns(2)
                            with etc1:
                                ted_name = st.text_input("Full Name", value=tu.full_name if tu else "")
                                ted_email = st.text_input("Email", value=tu.email if tu else "")
                                ted_empid = st.text_input("Employee ID", value=selected_t.employee_id)
                                ted_active = st.checkbox("Account Active", value=tu.is_active if tu else True, key="ted_active")
                            with etc2:
                                all_depts_t = AcademicService.get_departments(db)
                                dept_dict_t = {dept.name: dept.id for dept in all_depts_t}
                                curr_t_dept = td.name if td else (all_depts_t[0].name if all_depts_t else "")
                                ted_dept_name = st.selectbox("Department", list(dept_dict_t.keys()), index=list(dept_dict_t.keys()).index(curr_dept_name) if curr_t_dept in dept_dict_t else 0, key="ted_dept")
                                ted_desig = st.selectbox("Designation", ["Assistant Professor", "Associate Professor", "Professor", "Head of Department"], index=0)

                            btn_save_t = st.form_submit_button("Save Faculty Changes", type="primary")

                            if btn_save_t:
                                ok, msg = UserService.update_full_teacher_profile(
                                    db=db,
                                    teacher_id=selected_t.id,
                                    full_name=ted_name,
                                    email=ted_email,
                                    employee_id=ted_empid,
                                    department_id=dept_dict_t[ted_dept_name],
                                    designation=ted_desig,
                                    is_active=ted_active
                                )
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

    # --------------------------------------------------------------------------
    # TAB 4: DEPARTMENTS & SUBJECT MANAGEMENT
    # --------------------------------------------------------------------------
    with tab4:
        st.subheader("Academic Department & Course Subject Management")

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            st.markdown("##### ➕ Create New Academic Department")
            with st.form("add_dept_form"):
                d_name = st.text_input("Department Name (e.g. Mechanical Engineering)")
                d_code = st.text_input("Department Code (e.g. ME)")
                submit_dept = st.form_submit_button("Add Department")

                if submit_dept:
                    if not (d_name and d_code):
                        st.error("Please enter both department name and code.")
                    else:
                        with get_db() as db:
                            ok, msg = AcademicService.create_department(db, d_name, d_code)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

        with col_d2:
            st.markdown("##### ➕ Add New Course Subject")
            with st.form("add_sub_form"):
                sub_code = st.text_input("Subject Code (e.g. CS101)")
                sub_name = st.text_input("Subject Name (e.g. Data Structures)")
                with get_db() as db:
                    depts_for_sub = AcademicService.get_departments(db)
                    dept_map_sub = {d.name: d.id for d in depts_for_sub}
                sub_dept_name = st.selectbox("Department", list(dept_map_sub.keys())) if dept_map_sub else "CS"
                sub_credits = st.number_input("Credits", min_value=1, max_value=6, value=3)
                sub_sem = st.number_input("Semester", min_value=1, max_value=8, value=1)
                submit_sub = st.form_submit_button("Add Subject")

                if submit_sub:
                    if not (sub_code and sub_name):
                        st.error("Subject code and name are required.")
                    else:
                        with get_db() as db:
                            ok, msg = AcademicService.create_subject(
                                db=db,
                                code=sub_code,
                                name=sub_name,
                                dept_id=dept_map_sub[sub_dept_name],
                                credits=sub_credits,
                                semester=sub_sem
                            )
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

        st.markdown("---")
        st.markdown("#### 🏫 Existing Departments & Offered Subjects")
        with get_db() as db:
            dept_objs = AcademicService.get_departments(db)
            for d in dept_objs:
                st.markdown(f"### 🏢 {d.name} (`{d.code}`)")
                subs = d.subjects
                if subs:
                    sub_data = [{"Subject Code": s.subject_code, "Name": s.name, "Credits": s.credits, "Semester": s.semester} for s in subs]
                    st.dataframe(pd.DataFrame(sub_data), use_container_width=True)
                else:
                    st.caption("No subjects registered under this department yet.")

    # --------------------------------------------------------------------------
    # TAB 5: CSV IMPORT / EXPORT
    # --------------------------------------------------------------------------
    with tab5:
        st.subheader("Bulk Student Data Processing")
        col_imp, col_exp = st.columns(2)

        with col_imp:
            st.markdown("##### 📥 Import Students from CSV")
            uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
            if uploaded_file is not None:
                if st.button("Process & Import CSV", type="primary"):
                    with get_db() as db:
                        bytes_data = uploaded_file.getvalue()
                        success, fail, errors = ImportExportService.import_students_csv(db, bytes_data)
                        st.success(f"Successfully imported {success} student records.")
                        if fail > 0:
                            st.warning(f"Failed rows: {fail}")
                            for err in errors[:5]:
                                st.error(err)

        with col_exp:
            st.markdown("##### 📤 Export Student Records")
            if st.button("Generate CSV Export"):
                with get_db() as db:
                    csv_str = ImportExportService.export_students_csv(db)
                    st.download_button(
                        label="Download Students CSV",
                        data=csv_str,
                        file_name="student_records_export.csv",
                        mime="text/csv"
                    )

    # --------------------------------------------------------------------------
    # TAB 6: ML MODEL RETRAINER
    # --------------------------------------------------------------------------
    with tab6:
        st.subheader("Retrain & Benchmark AI Models")
        st.info("Train and compare XGBoost, Random Forest, Gradient Boosting, Decision Tree, and Ridge Regressor models.")

        sample_size = st.slider("Dataset Training Size", min_value=500, max_value=5000, value=2000, step=500)
        if st.button("⚡ Run Retraining & Comparison Pipeline", type="primary"):
            with st.spinner("Generating dataset, scaling features, tuning hyper-parameters, and comparing models..."):
                df_synth = SyntheticDatasetGenerator.generate_dataset(num_samples=sample_size)
                trainer = ModelTrainer(saved_models_dir="saved_models")
                results, best_name, best_obj = trainer.train_and_evaluate(df_synth)

                st.success(f"🎉 Pipeline Completed! Automatically selected best model: **{best_name}**")

                # Display Comparison Table
                df_res = pd.DataFrame(results).T
                st.table(df_res)

                # Plot Comparison Chart
                fig_comp = AcademicCharts.plot_model_comparison_bar(results)
                st.plotly_chart(fig_comp, use_container_width=True)

    # --------------------------------------------------------------------------
    # TAB 7: AUDIT LOGS
    # --------------------------------------------------------------------------
    with tab7:
        st.subheader("Security & Operational Audit Logs")
        with get_db() as db:
            audit_logs = AuditService.get_recent_logs(db, limit=100)
            log_data = [{
                "ID": l.id,
                "User ID": l.user_id,
                "Action": l.action,
                "Details": l.details,
                "IP Address": l.ip_address,
                "Timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            } for l in audit_logs]
            st.dataframe(pd.DataFrame(log_data), use_container_width=True)

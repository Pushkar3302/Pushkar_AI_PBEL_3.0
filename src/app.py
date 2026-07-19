# src/app.py
import sys
import os
# Ensure the project root is in the python path to prevent import errors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from src import db_manager
from src import predictor

# 1. Page Configuration (Strictly Native Layout)
st.set_page_config(
    page_title="Universal Student Performance Predictive Dashboard",
    page_icon="🎓",
    layout="wide"
)

# Initialize session state for global customizable thresholds if they don't exist
if 'target_pass_mark' not in st.session_state:
    st.session_state['target_pass_mark'] = 50.0  # Default target passing mark (%)
if 'min_attendance' not in st.session_state:
    st.session_state['min_attendance'] = 75.0  # Default minimum attendance threshold (%)
if 'sessional_max' not in st.session_state:
    st.session_state['sessional_max'] = 30.0   # Default Continuous Assessment maximum score
if 'final_max' not in st.session_state:
    st.session_state['final_max'] = 70.0      # Default Final Exam maximum score (updated to 70.0)

# Initialize session state for parsed report card values
if 'parsed_name' not in st.session_state:
    st.session_state['parsed_name'] = ""
if 'parsed_id' not in st.session_state:
    st.session_state['parsed_id'] = ""
if 'parsed_attendance' not in st.session_state:
    st.session_state['parsed_attendance'] = 85.0
if 'parsed_continuous' not in st.session_state:
    st.session_state['parsed_continuous'] = 21.0
if 'parsed_final' not in st.session_state:
    st.session_state['parsed_final'] = 45.5

# Ensure database tables exist (idempotent setup)
try:
    db_manager.initialize_database()
except Exception as e:
    st.error(f"Database Initialization Error: {e}")

# Application Header
st.title("🎓 Educational Performance Analytics Dashboard")
st.caption("Universal evaluation platform using Random Forest modeling to assess candidate performance and compliance metrics dynamically.")

# 2. Main Navigation Tabs
tab1, tab2, tab3 = st.tabs([
    "🎯 Evaluation Dashboard", 
    "📊 Predictive Cohort Analytics", 
    "⚙️ System Configuration"
])

with tab1:
    st.header("Candidate Evaluation Panel")
    st.write("Input academic performance metrics below to evaluate risk levels, predict categories, and log outcomes.")
    
    col_input, col_result = st.columns([1.2, 1])
    
    with col_input:
        st.subheader("Academic Assessment Form")
        
        # Report Card Parser Expander
        with st.expander("📄 Auto-Fill form via Report Card Upload", expanded=False):
            uploaded_file = st.file_uploader(
                "Upload student report card (.txt format)", 
                type=["txt"],
                help="Upload a plain text report card containing Name, ID, Attendance, and Scores to auto-populate the form fields below."
            )
            if uploaded_file is not None:
                try:
                    content = uploaded_file.read().decode("utf-8")
                    parsed_data = {}
                    for line in content.split("\n"):
                        if ":" in line:
                            key, val = line.split(":", 1)
                            key = key.strip().lower()
                            val = val.strip()
                            if "name" in key:
                                parsed_data["name"] = val
                            elif "id" in key or "roll" in key or "registration" in key:
                                parsed_data["id"] = val
                            elif "attendance" in key:
                                clean_val = val.replace("%", "").strip()
                                parsed_data["attendance"] = float(clean_val)
                            elif "continuous" in key or "internal" in key or "sessional" in key:
                                parsed_data["continuous"] = float(val)
                            elif "final" in key or "mock" in key or "end sem" in key:
                                parsed_data["final"] = float(val)
                                
                    if parsed_data:
                        st.session_state['parsed_name'] = parsed_data.get("name", "")
                        st.session_state['parsed_id'] = parsed_data.get("id", "")
                        st.session_state['parsed_attendance'] = min(max(float(parsed_data.get("attendance", 85.0)), 0.0), 100.0)
                        st.session_state['parsed_continuous'] = min(max(float(parsed_data.get("continuous", float(st.session_state['sessional_max'] * 0.7))), 0.0), float(st.session_state['sessional_max']))
                        st.session_state['parsed_final'] = min(max(float(parsed_data.get("final", float(st.session_state['final_max'] * 0.65))), 0.0), float(st.session_state['final_max']))
                        st.success("Report card parsed successfully! Parameters updated below.")
                except Exception as e:
                    st.error(f"Failed to parse report card: {e}")

        with st.form("candidate_evaluation_form", clear_on_submit=False):
            name = st.text_input(
                "Candidate Full Name", 
                value=st.session_state['parsed_name'],
                placeholder="e.g. Devon Clark"
            )
            student_id = st.text_input(
                "Candidate ID / Registration Number", 
                value=st.session_state['parsed_id'],
                placeholder="e.g. REG-2026-9042"
            )
            
            attendance = st.slider(
                "Attendance Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(st.session_state['parsed_attendance']),
                step=1.0,
                help=f"Minimum required attendance threshold: {st.session_state['min_attendance']}%"
            )
            
            continuous_score = st.slider(
                f"Continuous Assessment Score (0 - {st.session_state['sessional_max']})",
                min_value=0.0,
                max_value=float(st.session_state['sessional_max']),
                value=float(st.session_state['parsed_continuous']),
                step=0.5,
                help="Accumulated coursework/sessional evaluation score."
            )
            
            final_score = st.slider(
                f"Final Examination Score (0 - {st.session_state['final_max']})",
                min_value=0.0,
                max_value=float(st.session_state['final_max']),
                value=float(st.session_state['parsed_final']),
                step=0.5,
                help="Semester-end mock or prep evaluation score."
            )
            
            submit = st.form_submit_button("Run Evaluation Profile")
            
        # Dynamic warning logic based on configured attendance threshold
        if attendance < st.session_state['min_attendance']:
            st.warning(f"⚠️ Warning: Attendance is below the configured threshold of {st.session_state['min_attendance']}%. Candidate will be classified under Risk.")
            
    with col_result:
        st.subheader("Evaluation Results")
        if submit:
            if not name.strip() or not student_id.strip():
                st.warning("Please provide both the candidate Name and Registration Number before running the prediction.")
            else:
                # Combine name and registration ID for database profile logging
                full_profile_name = f"{name.strip()} (ID: {student_id.strip()})"
                
                # Normalize features to correspond to the ML pipeline's expected shapes (Internals [0-30], Final [0-100])
                normalized_continuous = (continuous_score / st.session_state['sessional_max']) * 30.0
                normalized_final = (final_score / st.session_state['final_max']) * 100.0
                
                features = {
                    "study_hours": normalized_continuous,
                    "attendance_percentage": attendance,
                    "mock_score": normalized_final
                }
                
                try:
                    # Run model prediction
                    result = predictor.predict_performance(features)
                    pred_class = result["prediction"]
                    confidence_val = result["confidence"] * 100
                    
                    # Convert class outcomes to universal terminology
                    category_mapping = {
                        "Outstanding": "Excellent",
                        "First Class": "Good",
                        "Pass": "Satisfactory",
                        "Critical Risk": "Risk",
                        "Detained": "Risk"
                    }
                    universal_category = category_mapping.get(pred_class, "Satisfactory")
                    
                    # Apply custom attendance cutoff logic override
                    if attendance < st.session_state['min_attendance']:
                        universal_category = "Risk (Low Attendance)"
                        confidence_val = 100.0  # Threshold rule is absolute
                        
                    # Write to database (MySQL or local SQLite fallback)
                    db_id = db_manager.add_student(full_profile_name)
                    db_manager.add_performance_metrics(
                        student_id=db_id,
                        study_hours=continuous_score,
                        attendance_percentage=attendance,
                        mock_score=final_score,
                        predicted_outcome=universal_category
                    )
                    
                    # Display metrics
                    m_col1, m_col2 = st.columns(2)
                    
                    delta_label = "Attention Required" if "Risk" in universal_category else "Standard Standing"
                    delta_color = "inverse" if "Risk" in universal_category else "normal"
                    
                    m_col1.metric(
                        label="Predicted Performance Category",
                        value=universal_category,
                        delta=delta_label,
                        delta_color=delta_color
                    )
                    
                    m_col2.metric(
                        label="Model Prediction Confidence (%)",
                        value=f"{confidence_val:.1f}%"
                    )
                    
                    # Confidence progress bar
                    st.write("**Evaluation Confidence Meter**")
                    st.progress(confidence_val / 100.0)
                    
                    # Display contextual advice
                    if "Risk" in universal_category:
                        st.error("🚨 Candidate is categorized under high-risk thresholds. Immediate academic intervention is advised.")
                    elif universal_category in ["Excellent", "Good"]:
                        st.success("🎉 High performance standing predicted. Performance profile meets excellence benchmarks.")
                    else:
                        st.success("✅ Candidate stands within satisfactory limits.")
                        
                except Exception as e:
                    st.error(f"Inference execution failed: {e}")
        else:
            st.info("Input student metrics on the left form and execute run evaluation to review results.")

with tab2:
    st.header("Predictive Cohort Analytics")
    st.write("Aggregated analysis of evaluated candidates, attendance trends, and database logs.")
    
    try:
        df = db_manager.get_students_with_metrics()
        df_active = df.dropna(subset=['study_hours']).copy()
        
        if df_active.empty:
            st.info("No evaluations logged in the database yet. Submit forms in the evaluation tab to populate cohort logs.")
        else:
            total_students = len(df_active)
            risk_cohort = len(df_active[df_active['predicted_outcome'].str.contains("Risk", na=False)])
            risk_rate = (risk_cohort / total_students) * 100 if total_students > 0 else 0.0
            
            # Attendance compliance counter
            attendance_cutoff = st.session_state['min_attendance']
            below_attendance = len(df_active[df_active['attendance_percentage'] < attendance_cutoff])
            below_attendance_ratio = (below_attendance / total_students) * 100 if total_students > 0 else 0.0
            
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Total Cohort Logs", f"{total_students}")
            kpi2.metric("Attendance Shortages", f"{below_attendance}", delta=f"{below_attendance_ratio:.1f}% of cohort", delta_color="inverse")
            kpi3.metric("Risk Categorizations", f"{risk_cohort}", delta=f"{risk_rate:.1f}% of cohort", delta_color="inverse")
            
            # Visual Analytics Grid
            st.subheader("Cohort Metrics & Distributions")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.write("**Performance Distribution**")
                category_counts = df_active['predicted_outcome'].value_counts()
                st.bar_chart(category_counts)
                
            with chart_col2:
                st.write("**Coursework & Exam Scores vs Attendance Mapping**")
                scatter_df = df_active[['attendance_percentage', 'mock_score', 'predicted_outcome']].copy()
                scatter_df.columns = ['Attendance (%)', 'Final Exam Score', 'Performance Tier']
                st.scatter_chart(
                    data=scatter_df,
                    x='Attendance (%)',
                    y='Final Exam Score',
                    color='Performance Tier'
                )
                
            # Log Dataframe
            st.subheader("Registry Logs Database")
            display_df = df_active[[
                'student_id', 'name', 'study_hours', 
                'attendance_percentage', 'mock_score', 
                'predicted_outcome', 'recorded_at'
            ]].copy()
            
            display_df.columns = [
                'System ID', 'Candidate Profile', 'Continuous Assessment', 
                'Attendance (%)', 'Final Exam Score', 'Predicted Outcome', 'Recorded Timestamp'
            ]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Delete record section
            st.subheader("Registry Administration")
            del_col1, del_col2 = st.columns([1.5, 2])
            with del_col1:
                student_options = {
                    sid: f"{df_active[df_active['student_id'] == sid]['name'].iloc[0]}" 
                    for sid in sorted(df_active['student_id'].unique())
                }
                
                selected_sid = st.selectbox(
                    "Select candidate profile to delete",
                    options=list(student_options.keys()),
                    format_func=lambda x: student_options.get(x)
                )
                
                delete_btn = st.button("Delete Candidate Record", type="primary")
                if delete_btn:
                    try:
                        success = db_manager.delete_student(selected_sid)
                        if success:
                            st.success(f"Profile for system ID {selected_sid} deleted successfully.")
                            st.rerun()
                        else:
                            st.warning("Delete execution completed, but 0 records were updated.")
                    except Exception as e:
                        st.error(f"Failed to delete record: {e}")
                        
    except Exception as e:
        st.error(f"Error fetching historical database records: {e}")

with tab3:
    st.header("⚙️ Global System Configuration")
    st.write("Configure the global academic thresholds and scales below. These parameters dynamically adjust evaluation forms and decision logic.")
    
    cfg_col1, cfg_col2 = st.columns(2)
    
    # Options lists
    options_pass = [33.0, 35.0, 40.0, 50.0, 60.0]
    options_att = [60.0, 65.0, 70.0, 75.0, 80.0, 85.0]
    options_sessional = [10.0, 15.0, 20.0, 25.0, 30.0, 40.0]
    options_final = [50.0, 60.0, 70.0, 80.0, 100.0]
    
    # Resolve pre-selected indices based on current configuration state
    try:
        idx_pass = options_pass.index(st.session_state['target_pass_mark'])
    except ValueError:
        idx_pass = options_pass.index(50.0)
        
    try:
        idx_att = options_att.index(st.session_state['min_attendance'])
    except ValueError:
        idx_att = options_att.index(75.0)
        
    try:
        idx_sessional = options_sessional.index(st.session_state['sessional_max'])
    except ValueError:
        idx_sessional = options_sessional.index(30.0)
        
    try:
        idx_final = options_final.index(st.session_state['final_max'])
    except ValueError:
        idx_final = options_final.index(70.0)

    with cfg_col1:
        target_pass_mark = st.selectbox(
            "Target Passing Mark (%)", 
            options=options_pass,
            index=idx_pass,
            help="Define the score boundary required to successfully pass the course."
        )
        min_attendance = st.selectbox(
            "Minimum Attendance Threshold (%)", 
            options=options_att,
            index=idx_att,
            help="Attendance percentage required for exam eligibility."
        )
        
    with cfg_col2:
        sessional_max = st.selectbox(
            "Continuous Assessment Score Range", 
            options=options_sessional,
            index=idx_sessional,
            help="Maximum scale for continuous coursework evaluations."
        )
        final_max = st.selectbox(
            "Final Examination Score Range", 
            options=options_final,
            index=idx_final,
            help="Maximum scale for end-of-term examinations."
        )
        
    # Save parameters
    if st.button("Apply System Configurations"):
        st.session_state['target_pass_mark'] = target_pass_mark
        st.session_state['min_attendance'] = min_attendance
        st.session_state['sessional_max'] = sessional_max
        st.session_state['final_max'] = final_max
        st.success("Global configurations applied! Inputs and forms updated.")
        st.rerun()

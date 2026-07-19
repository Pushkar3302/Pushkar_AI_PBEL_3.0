# src/db_manager.py
import mysql.connector
from mysql.connector import Error as MySQLError
import sqlite3
import pandas as pd
import os
from src import config

# Global flag to track if we fell back to SQLite
_USE_SQLITE = (config.DB_ENGINE == "sqlite")

def get_connection(include_db=True):
    """
    Establish a connection to the database (MySQL or SQLite).
    Falls back to SQLite dynamically if MySQL fails.
    """
    global _USE_SQLITE
    if _USE_SQLITE:
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
        
    try:
        config_dict = {
            "host": config.DB_HOST,
            "user": config.DB_USER,
            "password": config.DB_PASSWORD,
            "port": config.DB_PORT
        }
        if include_db:
            config_dict["database"] = config.DB_DATABASE
        return mysql.connector.connect(**config_dict)
    except Exception as e:
        print(f"MySQL connection failed: {e}. Falling back to SQLite.")
        _USE_SQLITE = True
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def get_placeholder():
    """
    Returns the appropriate parameter placeholder for SQL queries
    ('?' for SQLite, '%s' for MySQL).
    """
    return "?" if _USE_SQLITE else "%s"

def initialize_database():
    """
    Executes the schema setup.
    If using MySQL, runs schema.sql.
    If using SQLite, runs SQLite-compatible schema creation.
    """
    # Attempt a connection (triggers SQLite fallback if MySQL is down)
    conn = get_connection(include_db=False)
    global _USE_SQLITE
    
    if _USE_SQLITE:
        print("Initializing SQLite database...")
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    study_hours REAL NOT NULL,
                    attendance_percentage REAL NOT NULL,
                    mock_score REAL NOT NULL,
                    predicted_outcome TEXT DEFAULT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
                );
            """)
            conn.commit()
            print(f"SQLite database initialized successfully at: {config.SQLITE_DB_PATH}")
        except Exception as e:
            print(f"Failed to initialize SQLite database: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()
    else:
        # MySQL path
        cursor = conn.cursor()
        try:
            schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schema.sql")
            if not os.path.exists(schema_path):
                raise FileNotFoundError(f"Schema file not found at: {schema_path}")
                
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
                
            print("Executing schema.sql on MySQL server...")
            for result in cursor.execute(schema_sql, multi=True):
                if result.with_rows:
                    result.fetchall()
            conn.commit()
            print("MySQL database initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize MySQL database: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

def add_student(name):
    """
    Inserts a new student and returns their student_id.
    """
    conn = get_connection()
    cursor = conn.cursor()
    placeholder = get_placeholder()
    try:
        query = f"INSERT INTO students (name) VALUES ({placeholder})"
        cursor.execute(query, (name,))
        conn.commit()
        student_id = cursor.lastrowid
        return student_id
    except Exception as e:
        print(f"Error adding student '{name}': {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def add_performance_metrics(student_id, study_hours, attendance_percentage, mock_score, predicted_outcome=None):
    """
    Inserts performance metrics for a student.
    """
    conn = get_connection()
    cursor = conn.cursor()
    placeholder = get_placeholder()
    try:
        query = f"""
            INSERT INTO performance_metrics 
            (student_id, study_hours, attendance_percentage, mock_score, predicted_outcome) 
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """
        cursor.execute(query, (student_id, study_hours, attendance_percentage, mock_score, predicted_outcome))
        conn.commit()
        metric_id = cursor.lastrowid
        return metric_id
    except Exception as e:
        print(f"Error adding performance metrics for student_id {student_id}: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_students_with_metrics():
    """
    Retrieves all students with their performance metrics as a pandas DataFrame.
    """
    conn = get_connection()
    global _USE_SQLITE
    
    if _USE_SQLITE:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    else:
        cursor = conn.cursor(dictionary=True)
        
    try:
        query = """
            SELECT 
                s.student_id,
                s.name,
                pm.metric_id,
                pm.study_hours,
                pm.attendance_percentage,
                pm.mock_score,
                pm.predicted_outcome,
                pm.recorded_at
            FROM students s
            LEFT JOIN performance_metrics pm ON s.student_id = pm.student_id
            ORDER BY s.student_id DESC, pm.recorded_at DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        columns = [
            "student_id", "name", "metric_id", "study_hours", 
            "attendance_percentage", "mock_score", "predicted_outcome", "recorded_at"
        ]
        
        if not rows:
            return pd.DataFrame(columns=columns)
            
        if _USE_SQLITE:
            df = pd.DataFrame([dict(r) for r in rows])
        else:
            df = pd.DataFrame(rows)
            
        return df
    except Exception as e:
        print(f"Error fetching student metrics: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def delete_student(student_id):
    """
    Deletes a student record (and cascades to delete performance metrics).
    """
    conn = get_connection()
    cursor = conn.cursor()
    placeholder = get_placeholder()
    try:
        query = f"DELETE FROM students WHERE student_id = {placeholder}"
        cursor.execute(query, (student_id,))
        conn.commit()
        # Row count check varies slightly; cursor.rowcount works for both
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting student with id {student_id}: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def update_predicted_outcome(metric_id, outcome):
    """
    Updates the predicted outcome for a specific metric record.
    """
    conn = get_connection()
    cursor = conn.cursor()
    placeholder = get_placeholder()
    try:
        query = f"UPDATE performance_metrics SET predicted_outcome = {placeholder} WHERE metric_id = {placeholder}"
        cursor.execute(query, (outcome, metric_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating prediction for metric_id {metric_id}: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

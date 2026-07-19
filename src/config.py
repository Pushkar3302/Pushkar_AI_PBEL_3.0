# src/config.py
import os

# Database Engine Selection ('mysql' or 'sqlite')
# Defaults to 'mysql' but will fall back to 'sqlite' if MySQL server is unreachable.
DB_ENGINE = os.getenv("DB_ENGINE", "mysql")

# MySQL Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_DATABASE = os.getenv("DB_DATABASE", "student_performance_db")
DB_PORT = int(os.getenv("DB_PORT", 3306))

# SQLite Configuration (Fallback/Development)
SQLITE_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "student_performance.db"
)

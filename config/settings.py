"""
Application Configuration Settings.
Loads environment variables using Pydantic BaseSettings.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings class with validation."""
    
    APP_NAME: str = "AI Academic Intelligence Platform"
    DEBUG: bool = True
    SECRET_KEY: str = "super-secret-key-change-in-production"
    
    # Database Settings
    DB_TYPE: str = "sqlite"  # 'sqlite' or 'mysql'
    DB_USER: str = "root"
    DB_PASSWORD: str = "rootpassword"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "student_performance_db"
    SQLITE_DB_PATH: str = "student_performance.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """Dynamically construct Database URI for SQLAlchemy."""
        if self.DB_TYPE.lower() == "mysql":
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        # SQLite fallback for quick setup and testing
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        db_path = os.path.join(base_dir, self.SQLITE_DB_PATH)
        return f"sqlite:///{db_path}"


settings = Settings()

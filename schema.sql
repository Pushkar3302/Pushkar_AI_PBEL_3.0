-- schema.sql
-- Database schema for Student Performance Prediction System

CREATE DATABASE IF NOT EXISTS student_performance_db;
USE student_performance_db;

-- 1. Students table to store basic profile information
CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Performance metrics table to store features and prediction outcomes
CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    study_hours DECIMAL(5,2) NOT NULL,
    attendance_percentage DECIMAL(5,2) NOT NULL,
    mock_score DECIMAL(5,2) NOT NULL,
    predicted_outcome VARCHAR(50) DEFAULT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

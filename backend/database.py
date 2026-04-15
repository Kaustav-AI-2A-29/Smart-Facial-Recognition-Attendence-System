"""
database.py — SQLite connection manager and schema initializer.
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_DB_PATH = os.getenv("DATABASE_URL", "./data/database.sqlite")

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_username ON users(username);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(20) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INTEGER,
    roll_number VARCHAR(20),
    department VARCHAR(50),
    email VARCHAR(100),
    address VARCHAR(255),
    hobbies TEXT,
    profile_picture_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_student_id ON students(student_id);
CREATE INDEX IF NOT EXISTS idx_user_id_student ON students(user_id);

CREATE TABLE IF NOT EXISTS faculty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    department VARCHAR(50),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_faculty_user_id ON faculty(user_id);

CREATE TABLE IF NOT EXISTS face_encodings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(20) NOT NULL,
    encoding BLOB NOT NULL,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_student_id_encoding ON face_encodings(student_id);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(20) NOT NULL,
    date VARCHAR(10) NOT NULL,
    time_in VARCHAR(8),
    screenshot_path VARCHAR(255),
    face_confidence FLOAT,
    liveness_passed BOOLEAN DEFAULT 1,
    marked_by VARCHAR(20) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_student_date ON attendance(student_id, date);
CREATE INDEX IF NOT EXISTS idx_date ON attendance(date);
"""


class Database:
    """SQLite database connection manager."""

    def __init__(self, db_path: str = _DB_PATH):
        self.db_path = db_path
        self._ensure_directory()
        self.init_schema()

    def _ensure_directory(self) -> None:
        """Create data directory if it doesn't exist."""
        dir_path = os.path.dirname(self.db_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get a new database connection with row dict support."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def get_db(self):
        """Context manager for safe database access with auto commit/rollback."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as exc:
            conn.rollback()
            logger.error("Database transaction rolled back: %s", exc)
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        """Initialize database schema (idempotent — uses IF NOT EXISTS)."""
        try:
            with self.get_db() as conn:
                conn.executescript(_SCHEMA_SQL)
            logger.info("Database schema initialized: %s", self.db_path)
        except Exception as exc:
            logger.error("Schema initialization failed: %s", exc)
            raise

    def execute(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return all rows."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute a SELECT query and return a single row."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT statement and return the last row ID."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an UPDATE or DELETE statement and return row count."""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount


# Global singleton instance used across the app
db = Database(_DB_PATH)

"""
test_database.py — Tests for database connection and schema.
Run: pytest tests/test_database.py -v
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import Database

TABLES = {"users", "students", "faculty", "face_encodings", "attendance"}


@pytest.fixture
def test_db(tmp_path):
    """In-memory test database (isolated per test)."""
    db = Database(str(tmp_path / "test.sqlite"))
    return db


def test_database_connection(test_db):
    """Verify database file is created and readable."""
    assert os.path.exists(test_db.db_path)


def test_tables_exist(test_db):
    """Verify all 5 required tables were created."""
    rows = test_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    created = {r["name"] for r in rows}
    assert TABLES.issubset(created), f"Missing tables: {TABLES - created}"


def test_insert_user(test_db):
    """Verify user insertion and retrieval."""
    user_id = test_db.execute_insert(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("testuser", "hash123", "student"),
    )
    assert user_id is not None and user_id > 0

    row = test_db.execute_one("SELECT * FROM users WHERE id = ?", (user_id,))
    assert row is not None
    assert row["username"] == "testuser"
    assert row["role"] == "student"


def test_insert_student(test_db):
    """Verify student insertion with foreign key to users."""
    user_id = test_db.execute_insert(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("student_test", "hash", "student"),
    )
    test_db.execute_insert(
        "INSERT INTO students (student_id, user_id, name) VALUES (?, ?, ?)",
        ("STU-TEST-001", user_id, "Test Student"),
    )
    row = test_db.execute_one(
        "SELECT * FROM students WHERE student_id = ?", ("STU-TEST-001",)
    )
    assert row is not None
    assert row["name"] == "Test Student"
    assert row["user_id"] == user_id


def test_insert_faculty(test_db):
    """Verify faculty insertion."""
    user_id = test_db.execute_insert(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("faculty_test", "hash", "faculty"),
    )
    test_db.execute_insert(
        "INSERT INTO faculty (user_id, name) VALUES (?, ?)",
        (user_id, "Dr. Test"),
    )
    row = test_db.execute_one(
        "SELECT * FROM faculty WHERE user_id = ?", (user_id,)
    )
    assert row is not None
    assert row["name"] == "Dr. Test"


def test_context_manager_rollback(test_db):
    """Verify failed transaction rolls back."""
    try:
        with test_db.get_db() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("rollback_test", "hash", "student"),
            )
            raise ValueError("Simulated error")
    except ValueError:
        pass

    row = test_db.execute_one(
        "SELECT * FROM users WHERE username = ?", ("rollback_test",)
    )
    assert row is None, "Rolled-back insert should not persist."

"""
test_auth.py — Tests for authentication: hashing, login, roles.
Run: pytest tests/test_auth.py -v
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import Database
from backend import auth


@pytest.fixture(autouse=True)
def patch_db(tmp_path, monkeypatch):
    """Patch backend.auth.db with an isolated in-memory database."""
    test_db = Database(str(tmp_path / "auth_test.sqlite"))
    monkeypatch.setattr(auth, "db", test_db)
    return test_db


def test_password_hashing():
    """Verify bcrypt hash/verify roundtrip."""
    password = "secure_password_123"
    hashed = auth.hash_password(password)
    assert hashed != password
    assert auth.verify_password(password, hashed)
    assert not auth.verify_password("wrong_password", hashed)


def test_create_user(patch_db):
    """Verify user creation returns a valid ID."""
    uid = auth.create_user("testuser", "pass1234", "student")
    assert isinstance(uid, int) and uid > 0


def test_login_success(patch_db):
    """Verify successful login returns user dict."""
    uid = auth.create_user("studentlogin", "pass1234", "student")
    patch_db.execute_insert(
        "INSERT INTO students (student_id, user_id, name) VALUES (?, ?, ?)",
        ("STU-L01", uid, "Login Student"),
    )
    result = auth.login_user("studentlogin", "pass1234")
    assert result is not None
    assert result["username"] == "studentlogin"
    assert result["role"] == "student"
    assert result["student_id"] == "STU-L01"
    assert "password_hash" not in result


def test_login_failure_wrong_password(patch_db):
    """Verify wrong password returns None."""
    auth.create_user("failuser", "correct", "student")
    result = auth.login_user("failuser", "wrong")
    assert result is None


def test_login_failure_unknown_user(patch_db):
    """Verify unknown username returns None."""
    result = auth.login_user("nobody", "anything")
    assert result is None


def test_invalid_role(patch_db):
    """Verify invalid role raises ValueError."""
    with pytest.raises(ValueError, match="Invalid role"):
        auth.create_user("baduser", "pass", "superadmin")


def test_inactive_user_blocked(patch_db):
    """Verify deactivated account cannot log in."""
    uid = auth.create_user("inactive_user", "pass123", "student")
    auth.deactivate_user(uid)
    result = auth.login_user("inactive_user", "pass123")
    assert result is None


def test_faculty_login(patch_db):
    """Verify faculty login flow."""
    uid = auth.create_user("dr_test", "faculty_pass", "faculty")
    patch_db.execute_insert(
        "INSERT INTO faculty (user_id, name) VALUES (?, ?)",
        (uid, "Dr. Test"),
    )
    result = auth.login_user("dr_test", "faculty_pass")
    assert result is not None
    assert result["role"] == "faculty"
    assert result["name"] == "Dr. Test"

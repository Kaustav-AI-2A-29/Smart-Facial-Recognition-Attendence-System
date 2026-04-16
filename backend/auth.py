"""
auth.py — Authentication: login, password hashing, user management.
"""

import logging
import re
from typing import Optional, Dict

import bcrypt

from backend.database import db

logger = logging.getLogger(__name__)

_VALID_ROLES = {"student", "faculty"}


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password: Plain-text password string.

    Returns:
        Bcrypt-hashed password string.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash.

    Args:
        password: Plain-text password to verify.
        password_hash: Stored bcrypt hash string.

    Returns:
        True if password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception as exc:
        logger.error("Password verification error: %s", exc)
        return False


def login_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate a user and return their profile on success.

    Args:
        username: Username string.
        password: Plain-text password string.

    Returns:
        Dictionary with user info on success, None on failure.
        Keys: user_id, username, role, name, student_id (if student).
    """
    try:
        # FIX 1: Normalize username to lowercase for consistency
        username = username.lower()
        row = db.execute_one(
            "SELECT id, username, password_hash, role, is_active FROM users WHERE LOWER(username) = LOWER(?)",
            (username,),
        )
        if row is None:
            logger.warning("Login failed — unknown username: %s", username)
            return None
        
        # Normalize the returned username to lowercase too
        username = row["username"].lower()

        if not row["is_active"]:
            logger.warning("Login failed — inactive account: %s", username)
            return None

        if not verify_password(password, row["password_hash"]):
            logger.warning("Login failed — wrong password for user: %s", username)
            return None

        user = {
            "user_id": row["id"],
            "username": username,  # Store lowercase username
            "role": row["role"],
            "student_id": None,
            "name": "",
        }

        if row["role"] == "student":
            student = db.execute_one(
                "SELECT student_id, name FROM students WHERE user_id = ?",
                (row["id"],),
            )
            if student:
                user["student_id"] = student["student_id"]
                user["name"] = student["name"]

        elif row["role"] == "faculty":
            faculty = db.execute_one(
                "SELECT name FROM faculty WHERE user_id = ?",
                (row["id"],),
            )
            if faculty:
                user["name"] = faculty["name"]

        logger.info("Login successful: %s (%s)", username, row["role"])
        return user

    except Exception as exc:
        logger.error("Login error for user %s: %s", username, exc)
        return None


def create_user(username: str, password: str, role: str) -> int:
    """Create a new user record.

    Args:
        username: Unique username string.
        password: Plain-text password (will be hashed).
        role: Either 'student' or 'faculty'.

    Returns:
        New user ID integer.

    Raises:
        ValueError: If role is invalid or username already exists.
    """
    if role not in _VALID_ROLES:
        raise ValueError(f"Invalid role '{role}'. Must be one of: {_VALID_ROLES}")

    # FIX 1: Normalize username to lowercase
    username = username.lower()
    password_hash = hash_password(password)
    user_id = db.execute_insert(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, password_hash, role),
    )
    logger.info("Created user: %s (role=%s)", username, role)
    return user_id


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Fetch user info by user ID (excludes password_hash).

    Args:
        user_id: Integer user ID.

    Returns:
        Dictionary with user fields, or None if not found.
    """
    row = db.execute_one(
        "SELECT id, username, role, is_active, created_at FROM users WHERE id = ?",
        (user_id,),
    )
    if row is None:
        return None
    return dict(row)


def deactivate_user(user_id: int) -> bool:
    """Deactivate a user account (soft delete).

    Args:
        user_id: Integer user ID.

    Returns:
        True if deactivated, False if user not found.
    """
    affected = db.execute_update(
        "UPDATE users SET is_active = 0 WHERE id = ?", (user_id,)
    )
    return affected > 0

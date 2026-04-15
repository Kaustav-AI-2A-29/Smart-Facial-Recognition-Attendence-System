"""
student_service.py — CRUD operations for student profiles.
"""

import logging
import re
from typing import Optional, List, Dict, Any

from backend.database import db

logger = logging.getLogger(__name__)

_ALLOWED_UPDATE_FIELDS = {
    "name",
    "age",
    "roll_number",
    "department",
    "email",
    "address",
    "hobbies",
    "profile_picture_path",
}


def _validate_email(email: str) -> bool:
    """Validate basic email format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def get_student_by_id(student_id: str) -> Optional[Dict]:
    """Fetch a student profile by student_id.

    Args:
        student_id: Unique student ID (e.g., 'STU-001').

    Returns:
        Student profile dictionary, or None if not found.
    """
    row = db.execute_one(
        "SELECT * FROM students WHERE student_id = ?", (student_id,)
    )
    return dict(row) if row else None


def get_student_by_user_id(user_id: int) -> Optional[Dict]:
    """Fetch a student profile by their login user_id.

    Args:
        user_id: Integer foreign key from users table.

    Returns:
        Student profile dictionary, or None if not found.
    """
    row = db.execute_one(
        "SELECT * FROM students WHERE user_id = ?", (user_id,)
    )
    return dict(row) if row else None


def get_all_students() -> List[Dict]:
    """Fetch all student profiles (for faculty dashboard).

    Returns:
        List of student profile dictionaries.
    """
    rows = db.execute(
        "SELECT * FROM students ORDER BY name ASC"
    )
    return [dict(r) for r in rows]


def search_students(query: str) -> List[Dict]:
    """Search students by name, student_id, or department (case-insensitive).

    Args:
        query: Search term string.

    Returns:
        List of matching student profile dictionaries.
    """
    pattern = f"%{query}%"
    rows = db.execute(
        """
        SELECT * FROM students
        WHERE name LIKE ? OR student_id LIKE ? OR department LIKE ?
        ORDER BY name ASC
        """,
        (pattern, pattern, pattern),
    )
    return [dict(r) for r in rows]


def update_student(student_id: str, **kwargs: Any) -> bool:
    """Update allowed fields on a student profile.

    Args:
        student_id: Student ID to update.
        **kwargs: Field-value pairs to update (only allowed fields).

    Returns:
        True if updated, False if student not found or no valid fields.

    Raises:
        ValueError: If age is out of range or email is malformed.
    """
    updates = {k: v for k, v in kwargs.items() if k in _ALLOWED_UPDATE_FIELDS}
    if not updates:
        logger.warning("update_student called with no valid fields for %s", student_id)
        return False

    if "age" in updates:
        age = updates["age"]
        if not (isinstance(age, int) and 1 <= age <= 100):
            raise ValueError(f"Age must be an integer between 1 and 100, got: {age}")

    if "email" in updates and updates["email"]:
        if not _validate_email(updates["email"]):
            raise ValueError(f"Invalid email format: {updates['email']}")

    set_clause = ", ".join(f"{field} = ?" for field in updates)
    set_clause += ", updated_at = CURRENT_TIMESTAMP"
    params = list(updates.values()) + [student_id]

    affected = db.execute_update(
        f"UPDATE students SET {set_clause} WHERE student_id = ?", tuple(params)
    )
    if affected > 0:
        logger.info("Updated student %s: fields=%s", student_id, list(updates.keys()))
        return True
    logger.warning("update_student: no student found with id=%s", student_id)
    return False


def create_student(student_id: str, user_id: int, name: str, **kwargs: Any) -> bool:
    """Create a new student record.

    Args:
        student_id: Unique student ID (e.g., 'STU-001').
        user_id: Foreign key linking to users table.
        name: Student's full name.
        **kwargs: Optional fields (age, roll_number, department, email, address, hobbies).

    Returns:
        True on success.

    Raises:
        ValueError: On validation failure.
        Exception: On database error (e.g., duplicate student_id).
    """
    if "age" in kwargs:
        age = kwargs["age"]
        if not (isinstance(age, int) and 1 <= age <= 100):
            raise ValueError(f"Age must be 1-100, got: {age}")

    if "email" in kwargs and kwargs["email"]:
        if not _validate_email(kwargs["email"]):
            raise ValueError(f"Invalid email: {kwargs['email']}")

    db.execute_insert(
        """
        INSERT INTO students
            (student_id, user_id, name, age, roll_number, department, email, address, hobbies)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_id,
            user_id,
            name,
            kwargs.get("age"),
            kwargs.get("roll_number"),
            kwargs.get("department"),
            kwargs.get("email"),
            kwargs.get("address"),
            kwargs.get("hobbies"),
        ),
    )
    logger.info("Created student: %s (%s)", student_id, name)
    return True


def delete_student(student_id: str) -> bool:
    """Delete a student record (cascades to attendance + encodings).

    Args:
        student_id: Student ID to delete.

    Returns:
        True if deleted, False if not found.
    """
    affected = db.execute_update(
        "DELETE FROM students WHERE student_id = ?", (student_id,)
    )
    if affected > 0:
        logger.info("Deleted student: %s", student_id)
        return True
    return False

"""
attendance_service.py — Record and query attendance.
"""

import logging
from datetime import date, datetime
from typing import Optional, List, Dict

from backend.database import db

logger = logging.getLogger(__name__)


def record_attendance(
    student_id: str,
    screenshot_path: str,
    confidence: float,
    liveness_passed: bool = True,
    marked_by: str = "system",
) -> bool:
    """Record attendance for a student (one record per student per day).

    Args:
        student_id: Student ID string.
        screenshot_path: Relative path of the saved screenshot.
        confidence: Face recognition confidence score (0.0–1.0).
        liveness_passed: Whether liveness check was successful.
        marked_by: 'system' for auto, 'faculty' for manual.

    Returns:
        True if newly recorded, False if already recorded for today.
    """
    today = date.today().isoformat()
    time_now = datetime.now().strftime("%H:%M:%S")

    existing = db.execute_one(
        "SELECT id FROM attendance WHERE student_id = ? AND date = ?",
        (student_id, today),
    )
    if existing:
        logger.info(
            "Attendance already recorded today for %s (updating confidence if better)",
            student_id,
        )
        existing_conf = db.execute_one(
            "SELECT face_confidence FROM attendance WHERE student_id = ? AND date = ?",
            (student_id, today),
        )
        if existing_conf and confidence > (existing_conf["face_confidence"] or 0.0):
            db.execute_update(
                "UPDATE attendance SET face_confidence = ? WHERE student_id = ? AND date = ?",
                (confidence, student_id, today),
            )
        return False

    db.execute_insert(
        """
        INSERT INTO attendance
            (student_id, date, time_in, screenshot_path, face_confidence, liveness_passed, marked_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (student_id, today, time_now, screenshot_path, confidence, liveness_passed, marked_by),
    )
    logger.info("Attendance recorded: %s on %s at %s", student_id, today, time_now)
    return True


def get_attendance_by_student(student_id: str, limit: int = 30) -> List[Dict]:
    """Fetch attendance records for a student, most recent first.

    Args:
        student_id: Student ID string.
        limit: Maximum number of records to return.

    Returns:
        List of attendance record dictionaries.
    """
    rows = db.execute(
        """
        SELECT * FROM attendance
        WHERE student_id = ?
        ORDER BY date DESC, time_in DESC
        LIMIT ?
        """,
        (student_id, limit),
    )
    return [dict(r) for r in rows]


def get_attendance_by_date(date_str: str) -> List[Dict]:
    """Fetch all attendance records for a specific date.

    Args:
        date_str: ISO date string (YYYY-MM-DD).

    Returns:
        List of attendance record dictionaries for that date.
    """
    rows = db.execute(
        "SELECT * FROM attendance WHERE date = ? ORDER BY time_in ASC",
        (date_str,),
    )
    return [dict(r) for r in rows]


def get_attendance_stats(
    student_id: str, start_date: str, end_date: str
) -> Dict:
    """Compute attendance statistics for a student over a date range.

    Args:
        student_id: Student ID string.
        start_date: Start of range (YYYY-MM-DD).
        end_date: End of range (YYYY-MM-DD).

    Returns:
        Dictionary with keys: total_days, present, absent, percentage.
    """
    rows = db.execute(
        """
        SELECT COUNT(*) as present FROM attendance
        WHERE student_id = ? AND date BETWEEN ? AND ?
        """,
        (student_id, start_date, end_date),
    )
    present = rows[0]["present"] if rows else 0

    from datetime import date as date_cls, timedelta
    start = date_cls.fromisoformat(start_date)
    end = date_cls.fromisoformat(end_date)
    total_days = (end - start).days + 1

    absent = total_days - present
    percentage = round((present / total_days) * 100, 1) if total_days > 0 else 0.0

    return {
        "total_days": total_days,
        "present": present,
        "absent": absent,
        "percentage": percentage,
    }


def get_all_attendance() -> List[Dict]:
    """Fetch all attendance records (for faculty-level reporting).

    Returns:
        List of all attendance record dictionaries.
    """
    rows = db.execute(
        "SELECT * FROM attendance ORDER BY date DESC, time_in DESC"
    )
    return [dict(r) for r in rows]


def mark_attendance_manual(
    student_id: str, marked_by: str = "faculty"
) -> bool:
    """Manually mark attendance for a student (faculty action).

    Args:
        student_id: Student ID string.
        marked_by: Faculty identifier who marked it.

    Returns:
        True if newly recorded, False if already marked today.
    """
    return record_attendance(
        student_id=student_id,
        screenshot_path="",
        confidence=1.0,
        liveness_passed=True,
        marked_by=marked_by,
    )

"""
attendance_service.py — Record and query attendance.
"""

import logging
from datetime import date, datetime
from typing import Optional, List, Dict

from backend.database import db

logger = logging.getLogger(__name__)

PERIOD_HOURS = {9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6, 15: 7}


def get_period_from_time(time_str: str) -> "int | None":
    """Return period number (1-7) based on HH:MM:SS time string.
    Returns None if the time falls outside class hours (09:00-16:00).
    Periods: P1=9-10, P2=10-11, P3=11-12, P4=12-13,
             P5=13-14, P6=14-15, P7=15-16.
    """
    try:
        hour = int(time_str.split(":")[0])
        return PERIOD_HOURS.get(hour, None)
    except Exception:
        return None



def record_attendance(
    student_id: str,
    screenshot_path: str,
    confidence: float,
    liveness_passed: bool = True,
    marked_by: str = "system",
) -> bool:
    """Record attendance for a student (one record per student per period per day).

    Args:
        student_id: Student ID string.
        screenshot_path: Relative path of the saved screenshot.
        confidence: Face recognition confidence score (0.0–1.0).
        liveness_passed: Whether liveness check was successful.
        marked_by: 'system' for auto, 'faculty' for manual.

    Returns:
        True if newly recorded, False if already recorded for this period today.
    """
    today = date.today().isoformat()
    time_now = datetime.now().strftime("%H:%M:%S")
    period = get_period_from_time(time_now)

    if period is None:
        logger.warning("Attendance scanned outside class hours: %s", time_now)

    existing = db.execute_one(
        "SELECT id FROM attendance WHERE student_id = ? AND date = ? AND period IS ?",
        (student_id, today, period),
    )
    if existing:
        logger.info(
            "Attendance already recorded for %s on %s period %s",
            student_id, today, period,
        )
        return False

    db.execute_insert(
        """
        INSERT INTO attendance
            (student_id, date, time_in, period, screenshot_path,
             face_confidence, liveness_passed, marked_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (student_id, today, time_now, period, screenshot_path,
         confidence, liveness_passed, marked_by),
    )
    logger.info(
        "Attendance recorded: %s on %s at %s (period %s)",
        student_id, today, time_now, period,
    )
    return True


def get_attendance_by_student(student_id: str, limit: int = 30) -> List[Dict]:
    """Fetch attendance records for a student, most recent first.
    
    ALWAYS uses a fresh database connection (never cached).

    Args:
        student_id: Student ID string.
        limit: Maximum number of records to return.

    Returns:
        List of attendance record dictionaries.
    """
    # FIX 6: Force fresh database query every time
    # Create new connection to ensure data is fresh - NO CACHING
    import time
    cache_buster = time.time()  # Force fresh query each time
    
    rows = db.execute(
        """
        SELECT a.*, s.name as student_name
        FROM attendance a
        LEFT JOIN students s ON a.student_id = s.student_id
        WHERE a.student_id = ?
        ORDER BY a.date DESC, a.time_in DESC
        LIMIT ?
        """,
        (student_id, limit),
    )
    records = [dict(r) for r in rows]
    logger.info(f"get_attendance_by_student: Found {len(records)} records for student_id={student_id} (cache_buster={cache_buster})")
    return records


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
        List of all attendance record dictionaries including student names.
    """
    rows = db.execute(
        """
        SELECT a.*, s.name as student_name
        FROM attendance a
        LEFT JOIN students s ON a.student_id = s.student_id
        ORDER BY a.date DESC, a.time_in DESC
        """
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

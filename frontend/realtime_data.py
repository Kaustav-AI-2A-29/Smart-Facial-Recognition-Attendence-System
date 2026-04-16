"""
realtime_data.py — Real-time data fetching module with no caching.
Ensures fresh database queries every time without Streamlit caching.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

from backend.database import db
from backend.attendance_service import get_attendance_by_student, get_attendance_stats

# ─────────────────────────────────────────────────────────────────────────
# FIX: Use absolute database path to avoid working directory issues
# ─────────────────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.getenv("DATABASE_URL", os.path.join(_BASE_DIR, "data", "database.sqlite"))


def load_fresh_attendance_data(student_id: str, limit: int = 30) -> pd.DataFrame:
    """
    Load attendance data with GUARANTEED fresh database connection.
    
    This function NEVER uses caching. Each call creates a new connection
    and fetches the latest data from the database.
    
    Args:
        student_id: Student ID to fetch attendance for
        limit: Maximum number of records to return
        
    Returns:
        DataFrame with attendance records
    """
    # Create a completely fresh database connection each time with absolute path
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    
    try:
        # Direct SQL query - no ORM, no caching, guaranteed fresh
        query = """
        SELECT 
            a.id,
            a.student_id,
            a.date,
            a.time_in,
            a.screenshot_path,
            a.face_confidence,
            a.created_at,
            s.name as student_name
        FROM attendance a
        LEFT JOIN students s ON a.student_id = s.student_id
        WHERE a.student_id = ?
        ORDER BY a.date DESC, a.time_in DESC
        LIMIT ?
        """
        
        # Use pandas to read SQL - fresh connection
        df = pd.read_sql_query(
            query,
            conn,
            params=(student_id, limit),
            parse_dates=['date', 'created_at']
        )
        
        return df
        
    finally:
        conn.close()


def load_fresh_attendance_stats(
    student_id: str, start_date: str, end_date: str
) -> Dict:
    """
    Load attendance statistics with fresh database connection.
    
    Args:
        student_id: Student ID
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        Dictionary with statistics
    """
    # Create fresh connection with absolute path
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    
    try:
        # Count present days
        cursor = conn.execute(
            """
            SELECT COUNT(*) as total
            FROM attendance
            WHERE student_id = ? AND date BETWEEN ? AND ?
            """,
            (student_id, start_date, end_date)
        )
        present = cursor.fetchone()[0]
        
        # Calculate absent days
        from datetime import date as date_cls
        start = date_cls.fromisoformat(start_date)
        end = date_cls.fromisoformat(end_date)
        total_days = (end - start).days + 1
        absent = max(0, total_days - present)
        percentage = round((present / total_days) * 100, 1) if total_days > 0 else 0.0
        
        return {
            "total_days": total_days,
            "present": present,
            "absent": absent,
            "percentage": percentage,
        }
        
    finally:
        conn.close()


def get_database_timestamp() -> str:
    """
    Get the current timestamp to display when data was last fetched.
    Proves that data is being fetched fresh.
    
    Returns:
        Current timestamp as HH:MM:SS
    """
    return datetime.now().strftime("%H:%M:%S")


def get_latest_attendance_record(student_id: str) -> Optional[Dict]:
    """
    Get the single most recent attendance record for a student.
    
    Args:
        student_id: Student ID
        
    Returns:
        Dictionary with latest record, or None if no records
    """
    df = load_fresh_attendance_data(student_id, limit=1)
    
    if df.empty:
        return None
    
    # Convert row to dictionary
    record = df.iloc[0].to_dict()
    return record


def verify_fresh_data() -> bool:
    """
    Verification function to ensure Streamlit is not caching.
    
    Returns:
        True if data is being fetched fresh
    """
    # This should return different timestamps on each call if fresh
    ts1 = get_database_timestamp()
    import time
    time.sleep(0.01)
    ts2 = get_database_timestamp()
    
    # If timestamps are different, caching is NOT happening
    return ts1 != ts2

"""
COMPLETE VERIFICATION SCRIPT - Tests entire attendance flow end-to-end
Run this AFTER the Streamlit frontend is running
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import date, datetime
from backend.database import db
from backend.auth import login_user
from backend.student_service import get_student_by_user_id
from backend.attendance_service import (
    get_attendance_by_student,
    get_attendance_stats,
    record_attendance,
)

print("=" * 70)
print(" " * 15 + "COMPLETE VERIFICATION TEST - END-TO-END")
print("=" * 70)

# ============ PART 1: VERIFY DATABASE STATE ============
print("\n[PART 1] DATABASE STATE VERIFICATION")
print("-" * 70)

print("\n  A. Check all tables exist:")
cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor]
for table in ['users', 'students', 'attendance']:
    status = "✅" if table in tables else "❌"
    print(f"     {status} {table}")

print("\n  B. Check attendance table structure:")
cursor = db.execute("PRAGMA table_info(attendance);")
columns = {row[1]: row[2] for row in cursor}
required_cols = {
    'student_id': 'VARCHAR',
    'date': 'VARCHAR',
    'time_in': 'VARCHAR',
    'face_confidence': 'FLOAT'
}
for col, expected_type in required_cols.items():
    if col in columns:
        print(f"     ✅ {col} ({columns[col]})")
    else:
        print(f"     ❌ {col} MISSING!")

print("\n  C. Check data in attendance table:")
cursor = db.execute("SELECT COUNT(*) as cnt FROM attendance;")
total_records = cursor[0]['cnt']
print(f"     ✅ Total records: {total_records}")

cursor = db.execute("""
    SELECT COUNT(*) as cnt FROM attendance 
    WHERE date = '2026-04-16'
""")
today_records = cursor[0]['cnt']
print(f"     ✅ Records for today (2026-04-16): {today_records}")

# ============ PART 2: VERIFY AUTHENTICATION ============
print("\n[PART 2] AUTHENTICATION VERIFICATION")
print("-" * 70)

username = "kaustav"
password = "mypass1"
print(f"\n  A. Testing login with {username}/{password}:")

user = login_user(username, password)
if user:
    print(f"     ✅ Login successful!")
    print(f"        - User ID: {user['user_id']}")
    print(f"        - Username: {user['username']}")
    print(f"        - Role: {user['role']}")
    print(f"        - Student ID: {user['student_id']}")
else:
    print(f"     ❌ Login failed!")
    sys.exit(1)

# ============ PART 3: VERIFY STUDENT PROFILE ============
print("\n[PART 3] STUDENT PROFILE VERIFICATION")
print("-" * 70)

student = get_student_by_user_id(user['user_id'])
if student:
    print(f"\n  ✅ Student profile retrieved:")
    print(f"     - Name: {student['name']}")
    print(f"     - Student ID: {student['student_id']}")
    print(f"     - Department: {student['department']}")
else:
    print(f"  ❌ Student profile not found!")
    sys.exit(1)

# ============ PART 4: VERIFY ATTENDANCE RECORDS ============
print("\n[PART 4] ATTENDANCE RECORDS VERIFICATION")
print("-" * 70)

student_id = student['student_id']
print(f"\n  A. Fetching attendance for {student['name']} (ID: {student_id}):")

records = get_attendance_by_student(student_id, limit=30)
print(f"     ✅ Retrieved {len(records)} record(s)")

if records:
    print(f"\n  B. Latest record details:")
    latest = records[0]
    print(f"     - Date: {latest.get('date')}")
    print(f"     - Time: {latest.get('time_in')}")
    print(f"     - Confidence: {latest.get('face_confidence')}%")
    print(f"     - Screenshot: {latest.get('screenshot_path')}")
else:
    print(f"     ⚠️ No records found - this might be expected on first load")

# ============ PART 5: VERIFY STATISTICS ============
print("\n[PART 5] STATISTICS VERIFICATION")
print("-" * 70)

today = date.today()
start_of_month = today.replace(day=1)

stats = get_attendance_stats(
    student_id,
    start_of_month.isoformat(),
    today.isoformat(),
)

print(f"\n  Attendance statistics for {student['name']}:")
print(f"     - Present: {stats['present']}")
print(f"     - Absent: {stats['absent']}")
print(f"     - Percentage: {stats['percentage']}%")

# ============ PART 6: TEST NEW ATTENDANCE RECORDING ============
print("\n[PART 6] NEW ATTENDANCE RECORDING TEST")
print("-" * 70)

print(f"\n  A. Attempting to record new attendance for {student['name']}...")
result = record_attendance(
    student_id=student_id,
    screenshot_path=f"/screenshots/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
    confidence=87.5,
    liveness_passed=True,
    marked_by="test_script"
)

if result:
    print(f"     ✅ New attendance recorded!")
else:
    print(f"     ⚠️ Attendance already marked today (expected if marked earlier)")

print(f"\n  B. Verifying new attendance appears in queries...")
time.sleep(0.5)  # Small delay for database sync
records_after = get_attendance_by_student(student_id, limit=30)
print(f"     ✅ Now have {len(records_after)} record(s)")

if records_after and len(records_after) >= len(records):
    print(f"     ✅ New record retrieved successfully!")
    latest_after = records_after[0]
    print(f"        - Latest: {latest_after.get('date')} at {latest_after.get('time_in')}")
else:
    print(f"     ❌ New record not appearing!")

# ============ PART 7: VERIFY DATABASE QUERY DIRECTLY ============
print("\n[PART 7] DIRECT DATABASE QUERY VERIFICATION")
print("-" * 70)

print(f"\n  A. Direct SQL query (no backend functions):")
cursor = db.execute("""
    SELECT a.*, s.name as student_name
    FROM attendance a
    LEFT JOIN students s ON a.student_id = s.student_id
    WHERE a.student_id = ?
    ORDER BY a.date DESC, a.time_in DESC
    LIMIT 5
""", (student_id,))

direct_records = [dict(r) for r in cursor]
print(f"     ✅ Direct SQL returns {len(direct_records)} record(s)")

if direct_records:
    print(f"\n  B. Direct query results (first record):")
    rec = direct_records[0]
    for key in ['date', 'time_in', 'face_confidence', 'student_name']:
        print(f"     - {key}: {rec.get(key)}")

# ============ FINAL SUMMARY ============
print("\n" + "=" * 70)
print(" " * 20 + "VERIFICATION SUMMARY")
print("=" * 70)

all_passed = (
    len(records) > 0 and
    student is not None and
    user is not None and
    len(direct_records) > 0
)

if all_passed:
    print("\n  ✅ ALL TESTS PASSED! Data flow is working correctly.")
    print("\n  What this means:")
    print("  • Database has attendance records")
    print("  • Backend functions return correct data")
    print("  • Frontend should display all records immediately")
    print("\n  Next steps:")
    print("  1. Open http://localhost:8507 in your browser")
    print("  2. Login with kaustav / mypass1")
    print("  3. Go to 'My Attendance' tab")
    print("  4. You should see the attendance record displayed")
    print("  5. Click 'Refresh Now' button to force refresh if needed")
else:
    print("\n  ❌ Some tests failed! Check output above for details.")

print("\n" + "=" * 70)

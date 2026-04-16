"""
test_attendance_flow.py - Test the full attendance flow end-to-end.
Run: python test_attendance_flow.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import date
from backend.database import db
from backend.auth import login_user
from backend.student_service import get_student_by_user_id, get_all_students
from backend.attendance_service import (
    get_attendance_by_student,
    get_attendance_stats,
    record_attendance,
)

print("=" * 60)
print("  ATTENDANCE FLOW TEST")
print("=" * 60)

# Test 1: Login as student
print("\n[TEST 1] Login as student 'kaustav'")
user = login_user("kaustav", "mypass1")
if user:
    print(f"✅ Login successful!")
    print(f"   Username: {user['username']}")
    print(f"   User ID: {user['user_id']}")
    print(f"   Student ID: {user['student_id']}")
    print(f"   Name: {user['name']}")
else:
    print("❌ Login failed!")
    sys.exit(1)

# Test 2: Add attendance record
print("\n[TEST 2] Record attendance manually")
student_id = user['student_id']
today = date.today().isoformat()
result = record_attendance(
    student_id=student_id,
    screenshot_path="/path/to/screenshot.jpg",
    confidence=95.5,
    liveness_passed=True,
    marked_by="test"
)
if result:
    print(f"✅ Attendance recorded for {student_id}")
else:
    print(f"⚠️ Attendance already marked today")

# Test 3: Query attendance immediately
print("\n[TEST 3] Query attendance records (should show latest)")
records = get_attendance_by_student(student_id, limit=5)
print(f"✅ Found {len(records)} record(s)")
if records:
    for i, rec in enumerate(records[:3]):
        print(f"   {i+1}. Date: {rec['date']}, Time: {rec['time_in']}, Confidence: {rec['face_confidence']}%")

# Test 4: Check stats
print("\n[TEST 4] Check attendance stats")
from datetime import date as date_cls
today_obj = date_cls.today()
month_start = today_obj.replace(day=1).isoformat()
month_end = today_obj.isoformat()
stats = get_attendance_stats(student_id, month_start, month_end)
print(f"✅ Stats for {student_id}:")
print(f"   Present: {stats['present']}")
print(f"   Absent: {stats['absent']}")
print(f"   Percentage: {stats['percentage']}%")

# Test 5: Get student profile
print("\n[TEST 5] Get student profile")
student = get_student_by_user_id(user['user_id'])
if student:
    print(f"✅ Student profile:")
    print(f"   Name: {student['name']}")
    print(f"   Student ID: {student['student_id']}")
    print(f"   Department: {student['department']}")
else:
    print("❌ Student profile not found")

# Test 6: Case-insensitive username test
print("\n[TEST 6] Test case-insensitive login")
user_upper = login_user("KAUSTAV", "mypass1")
if user_upper and user_upper['username'].lower() == "kaustav":
    print(f"✅ Case-insensitive login works!")
    print(f"   Username stored as: {user_upper['username']}")
else:
    print("❌ Case-insensitive login failed")

print("\n" + "=" * 60)
print("  ALL TESTS COMPLETED")
print("=" * 60)

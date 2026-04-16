"""
Frontend debug test - simulates the student dashboard flow
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import date
from backend.auth import login_user
from backend.student_service import get_student_by_user_id
from backend.attendance_service import get_attendance_by_student, get_attendance_stats

print("=" * 60)
print("FRONTEND DEBUG TEST - STUDENT DASHBOARD FLOW")
print("=" * 60)

# Step 1: Simulate login
print("\n[STEP 1] Simulating student login (kaustav/mypass1)")
user = login_user("kaustav", "mypass1")
if not user:
    print("❌ Login failed!")
    sys.exit(1)

print(f"✅ Login successful!")
print(f"   User ID: {user['user_id']}")
print(f"   Username: {user['username']}")
print(f"   Student ID: {user['student_id']}")

# Step 2: Get student profile (like dashboard does)
print("\n[STEP 2] Fetching student profile (like dashboard loads)")
student = get_student_by_user_id(user['user_id'])
if not student:
    print("❌ Student not found!")
    sys.exit(1)

print(f"✅ Student profile found!")
print(f"   Name: {student['name']}")
print(f"   Student ID: {student['student_id']}")

# Step 3: Get attendance stats (for "This Month" metrics)
print("\n[STEP 3] Getting attendance stats (This Month)")
today = date.today()
start_of_month = today.replace(day=1)

stats = get_attendance_stats(
    student["student_id"],
    start_of_month.isoformat(),
    today.isoformat(),
)

print(f"✅ Stats retrieved!")
print(f"   Present: {stats['present']}")
print(f"   Absent: {stats['absent']}")
print(f"   Percentage: {stats['percentage']}%")

# Step 4: Get attendance records (the critical part)
print("\n[STEP 4] Fetching attendance records (CRITICAL)")
records = get_attendance_by_student(student["student_id"], limit=30)

print(f"✅ Records fetched!")
print(f"   Total records: {len(records)}")

if records:
    print("\n   📊 RAW RECORD DATA (First record):")
    rec = records[0]
    for key in rec.keys():
        print(f"      {key}: {rec[key]}")
    
    print("\n   ✅ WHAT FRONTEND WILL DISPLAY:")
    latest = records[0]
    latest_time = latest.get('time_in') or 'N/A'
    latest_confidence = latest.get('face_confidence') or 0.0
    print(f"      Latest: {latest.get('date')} at {latest_time} → Confidence: {latest_confidence:.1f}%")
else:
    print("   ❌ NO RECORDS FOUND! This is the problem!")

# Step 5: Check if it's a query issue
print("\n[STEP 5] Verifying query works at database level")
import sqlite3
db_path = os.path.join("data", "database.sqlite")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT a.*, s.name as student_name
    FROM attendance a
    LEFT JOIN students s ON a.student_id = s.student_id
    WHERE a.student_id = ?
    ORDER BY a.date DESC, a.time_in DESC
    LIMIT 30
""", (student["student_id"],))

db_records = cursor.fetchall()
print(f"✅ Raw SQL query returns: {len(db_records)} record(s)")
if db_records:
    for i, rec in enumerate(db_records[:3]):
        print(f"   {i+1}. Date: {rec['date']}, Time: {rec['time_in']}, Confidence: {rec['face_confidence']}")

conn.close()

print("\n" + "=" * 60)
if len(records) == len(db_records) and len(records) > 0:
    print("✅ EVERYTHING WORKS! Data is being fetched correctly")
else:
    print("❌ MISMATCH! Frontend function not returning database data")
print("=" * 60)

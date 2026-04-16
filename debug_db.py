"""
Debug script to inspect database schema and content
"""

import sqlite3
import os

# Connect to database
db_path = os.path.join("data", "database.sqlite")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check all tables
print("=" * 60)
print("STEP 1: ALL TABLES IN DATABASE")
print("=" * 60)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(f"  • {table['name']}")

# Check attendance table schema
print("\n" + "=" * 60)
print("STEP 2: ATTENDANCE TABLE SCHEMA")
print("=" * 60)
cursor.execute("PRAGMA table_info(attendance);")
columns = cursor.fetchall()
for col in columns:
    print(f"  • {col['name']} ({col['type']})")

# Check if there's a timestamp column
print("\n" + "=" * 60)
print("STEP 3: ACTUAL ATTENDANCE RECORDS (LIMIT 3)")
print("=" * 60)
cursor.execute("SELECT * FROM attendance LIMIT 3;")
records = cursor.fetchall()
print(f"Found {len(records)} record(s)")
if records:
    print(f"\nColumn names: {list(records[0].keys())}")
    for i, rec in enumerate(records):
        print(f"\n  Record {i+1}:")
        for key in rec.keys():
            print(f"    {key}: {rec[key]}")

# Check all attendance for today
print("\n" + "=" * 60)
print("STEP 4: TODAY'S ATTENDANCE (ALL STUDENTS)")
print("=" * 60)
cursor.execute("""
    SELECT * FROM attendance WHERE date = '2026-04-16'
    ORDER BY time_in DESC
""")
today_records = cursor.fetchall()
print(f"Found {len(today_records)} record(s) for today")
for i, rec in enumerate(today_records):
    print(f"\n  {i+1}. Student: {rec['student_id']}, Time: {rec['time_in']}, Confidence: {rec['face_confidence']}")

# Check users table
print("\n" + "=" * 60)
print("STEP 5: USERS IN DATABASE")
print("=" * 60)
cursor.execute("SELECT id, username, role FROM users;")
users = cursor.fetchall()
for user in users:
    print(f"  • {user['username']} (ID: {user['id']}, Role: {user['role']})")

# Check students table
print("\n" + "=" * 60)
print("STEP 6: STUDENTS IN DATABASE")
print("=" * 60)
cursor.execute("SELECT student_id, name, user_id FROM students;")
students = cursor.fetchall()
for student in students:
    print(f"  • {student['name']} (ID: {student['student_id']}, User ID: {student['user_id']})")

# Check kaustav student details
print("\n" + "=" * 60)
print("STEP 7: KAUSTAV'S ATTENDANCE (SPECIFIC STUDENT)")
print("=" * 60)
cursor.execute("""
    SELECT a.*, s.name as student_name
    FROM attendance a
    LEFT JOIN students s ON a.student_id = s.student_id
    WHERE a.student_id = 'STU-003'
    ORDER BY a.date DESC, a.time_in DESC
    LIMIT 5
""")
kaustav_records = cursor.fetchall()
print(f"Found {len(kaustav_records)} record(s) for Kaustav (STU-003)")
for i, rec in enumerate(kaustav_records):
    print(f"  {i+1}. Date: {rec['date']}, Time: {rec['time_in']}, Confidence: {rec['face_confidence']}%")

conn.close()
print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)

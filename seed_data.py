"""
seed_data.py - Populate the database with test students and faculty.
Run: python seed_data.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

from backend.database import db
from backend.auth import create_user
from backend.student_service import create_student

TEST_STUDENTS = [
    {
        "username": "debnil",
        "password": "mypass2",
        "student_id": "STU-001",
        "name": "Debnil",
        "age": 20,
        "roll_number": "CS-2024-001",
        "department": "Computer Science",
        "email": "debnil@college.edu",
        "hobbies": "Photography",
    },
    {
        "username": "jyotirmoy",
        "password": "mypass3",
        "student_id": "STU-002",
        "name": "Jyotirmoy",
        "age": 21,
        "roll_number": "CS-2024-002",
        "department": "Computer Science",
        "email": "jyotirmoy@college.edu",
        "hobbies": "Reading",
    },
    {
        "username": "kaustav",
        "password": "mypass1",
        "student_id": "STU-003",
        "name": "Kaustav",
        "age": 22,
        "roll_number": "IT-2024-001",
        "department": "Information Technology",
        "email": "kaustav@college.edu",
        "hobbies": "Gaming",
    },
    {
        "username": "soumita",
        "password": "mypass4",
        "student_id": "STU-004",
        "name": "Soumita",
        "age": 20,
        "roll_number": "CS-2024-003",
        "department": "Computer Science",
        "email": "soumita@college.edu",
        "hobbies": "Art",
    },
]

TEST_FACULTY = [
    {
        "username": "admin123",
        "password": "admin100",
        "name": "Dr. Admin",
        "email": "admin@college.edu",
        "department": "Administration",
    },
]


def clear_test_data():
    for s in TEST_STUDENTS:
        db.execute_update("DELETE FROM users WHERE username = ?", (s["username"],))
    for f in TEST_FACULTY:
        db.execute_update("DELETE FROM users WHERE username = ?", (f["username"],))
    print("  Cleared existing test data.")


def main():
    print("Seeding test data...")
    clear_test_data()

    print("\n  Creating STUDENT accounts:")
    for s in TEST_STUDENTS:
        existing = db.execute_one("SELECT id FROM users WHERE username = ?", (s["username"],))
        if existing:
            print(f"    [INFO] {s['username']} already exists, skipping.")
            continue
        user_id = create_user(s["username"], s["password"], "student")
        create_student(
            student_id=s["student_id"],
            user_id=user_id,
            name=s["name"],
            age=s["age"],
            roll_number=s["roll_number"],
            department=s["department"],
            email=s["email"],
            hobbies=s["hobbies"],
        )
        print(f"    [OK] {s['username']}  |  Student ID: {s['student_id']}  |  Name: {s['name']}")

    print("\n  Creating FACULTY accounts:")
    for f in TEST_FACULTY:
        existing = db.execute_one("SELECT id FROM users WHERE username = ?", (f["username"],))
        if existing:
            print(f"    [INFO] {f['username']} already exists, skipping.")
            continue
        user_id = create_user(f["username"], f["password"], "faculty")
        db.execute_insert(
            "INSERT INTO faculty (user_id, name, email, department) VALUES (?, ?, ?, ?)",
            (user_id, f["name"], f["email"], f["department"]),
        )
        print(f"    [OK] {f['username']}  |  Name: {f['name']}")

    print("""
Test data seeded successfully!

STUDENT CREDENTIALS:
  kaustav   -> password: mypass1  |  STU-003 - Kaustav
  debnil    -> password: mypass2  |  STU-001 - Debnil
  jyotirmoy -> password: mypass3  |  STU-002 - Jyotirmoy
  soumita   -> password: mypass4  |  STU-004 - Soumita

FACULTY CREDENTIALS:
  admin123  -> password: admin100
""")


if __name__ == "__main__":
    main()

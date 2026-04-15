#!/usr/bin/env python3
"""Verify student users in the database."""

from backend.database import db

def verify_students():
    print("\n" + "=" * 60)
    print("  VERIFYING STUDENT USERS IN DATABASE")
    print("=" * 60)
    
    users = db.execute(
        "SELECT id, username, role FROM users WHERE role = 'student' ORDER BY username"
    )
    
    if not users:
        print("  [ERROR] No student users found!")
        return False
    
    print(f"\n  Found {len(users)} student users:\n")
    for row in users:
        user_id = row["id"]
        username = row["username"]
        role = row["role"]
        
        # Get student details
        student = db.execute_one(
            "SELECT name, student_id FROM students WHERE user_id = ?",
            (user_id,)
        )
        
        if student:
            name = student["name"]
            student_id = student["student_id"]
            print(f"    ✓ {username:15} | ID: {student_id} | Name: {name}")
        else:
            print(f"    ✗ {username:15} | [ERROR] No student record")
    
    print("\n" + "=" * 60)
    print("  PASSWORD VERIFICATION")
    print("=" * 60)
    print("""
    Test credentials (login):
      • kaustav   / mypass1
      • debnil    / mypass2
      • jyotirmoy / mypass3
      • soumita   / mypass4
    """)
    print("=" * 60 + "\n")
    
    return True

if __name__ == "__main__":
    verify_students()

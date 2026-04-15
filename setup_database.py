"""
setup_database.py - Initialize the SQLite database schema.
Run once at project setup: python setup_database.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

from backend.database import Database
from backend.auth import hash_password

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DATABASE_URL", os.path.join(_BASE_DIR, "data", "database.sqlite"))


def main():
    print("Initializing database...")
    db = Database(DB_PATH)
    print(f"  [OK] Database file: {DB_PATH}")
    print("  [OK] Tables created: users, students, faculty, face_encodings, attendance")

    existing = db.execute_one("SELECT id FROM users WHERE username = ?", ("admin",))
    if existing:
        print("  [INFO] Admin user already exists, skipping creation.")
    else:
        pw_hash = hash_password("admin123")
        user_id = db.execute_insert(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", pw_hash, "faculty"),
        )
        db.execute_insert(
            "INSERT INTO faculty (user_id, name, email, department) VALUES (?, ?, ?, ?)",
            (user_id, "Dr. Admin", "admin@college.edu", "Administration"),
        )
        print("  [OK] Admin faculty user created.")
        print("    Username: admin  |  Password: admin123  <- CHANGE THIS!")

    print("\nDatabase setup complete!")


if __name__ == "__main__":
    main()

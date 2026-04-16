"""
verify_attendance_saved.py
Quick script to verify that attendance data is being saved to the database.
Run this after taking attendance through the face recognition system.
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database import db

def main():
    print("=" * 70)
    print("  ATTENDANCE VERIFICATION SCRIPT")
    print("=" * 70)
    
    # Show database path
    print(f"\n[INFO] Database path: {db.db_path}")
    print(f"[INFO] Database file exists: {os.path.exists(db.db_path)}")
    
    # Check students in database
    print("\n" + "─" * 70)
    print("REGISTERED STUDENTS:")
    print("─" * 70)
    students = db.execute("SELECT student_id, name FROM students ORDER BY name")
    for row in students:
        print(f"  {row['student_id']:<15} {row['name']}")
    
    # Check today's attendance
    today_str = date.today().isoformat()
    print("\n" + "─" * 70)
    print(f"TODAY'S ATTENDANCE ({today_str}):")
    print("─" * 70)
    
    rows = db.execute(
        """
        SELECT a.*, s.name as student_name
        FROM attendance a
        LEFT JOIN students s ON a.student_id = s.student_id
        WHERE a.date = ?
        ORDER BY a.time_in DESC
        """,
        (today_str,)
    )
    
    records = [dict(r) for r in rows]
    
    if not records:
        print("  ❌ NO ATTENDANCE RECORDS FOR TODAY")
    else:
        print(f"  ✅ Found {len(records)} attendance record(s):")
        for i, rec in enumerate(records, 1):
            print(f"\n    Record {i}:")
            print(f"      Student: {rec['student_name']} ({rec['student_id']})")
            print(f"      Time: {rec['time_in']}")
            print(f"      Confidence: {rec['face_confidence']:.1f}%" if rec['face_confidence'] else "      Confidence: N/A")
            print(f"      Screenshot: {rec['screenshot_path']}")
            if rec['screenshot_path'] and os.path.exists(rec['screenshot_path']):
                print(f"      Screenshot exists: ✅")
            else:
                print(f"      Screenshot exists: ❌")
    
    # Show total attendance statistics
    print("\n" + "─" * 70)
    print("ALL-TIME ATTENDANCE STATISTICS:")
    print("─" * 70)
    
    stats = db.execute("""
        SELECT s.name, COUNT(a.id) as total_attendance
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id
        GROUP BY s.student_id
        ORDER BY total_attendance DESC
    """)
    
    for row in stats:
        count = row['total_attendance'] if row['total_attendance'] else 0
        symbol = "✅" if count > 0 else "❌"
        print(f"  {symbol} {row['name']:<20} - {count} record(s)")
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

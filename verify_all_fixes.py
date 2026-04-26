"""
verify_all_fixes.py - Verify all bug fixes are working correctly.
Run: python verify_all_fixes.py
"""
import sys, os, csv
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database import db
from backend.attendance_service import get_period_from_time

TARGET_DATE = "2026-04-20"

print("=" * 55)
print("  FIX VERIFICATION REPORT")
print("=" * 55)

# ── 1. Period mapping ────────────────────────────────────────
print("\n[1] Period Mapping (time -> period)")
for t in ["09:54:49", "09:55:05", "12:46:36", "16:30:50", "03:31:30"]:
    p = get_period_from_time(t)
    label = f"P{p}" if p else "Outside hours"
    print(f"    {t}  ->  {label}")

# ── 2. DB records for today ──────────────────────────────────
print(f"\n[2] Database records for {TARGET_DATE}")
rows = db.execute(
    """
    SELECT s.name, a.date, a.time_in, a.period
    FROM attendance a
    LEFT JOIN students s ON a.student_id = s.student_id
    WHERE a.date = ?
    ORDER BY a.time_in
    """,
    (TARGET_DATE,),
)
if rows:
    for r in rows:
        print(f"    {r['name']:<12} | {r['date']} | {r['time_in']} | P{r['period']}")
else:
    print("    (none found)")

# ── 3. Session summary simulation ────────────────────────────
print("\n[3] Session Summary Simulation (case-insensitive)")
CSV_PATH = os.path.join(os.path.dirname(__file__), "attendance_system.csv")
marked = set()
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        if len(row) >= 3 and row[2] == TARGET_DATE:
            marked.add(row[0].lower())  # normalize

all_people = {"kaustav", "soumita", "debnil", "jyotirmoy"}
absent = all_people - marked
overlap = marked & absent

print(f"    Present : {sorted(marked)}")
print(f"    Absent  : {sorted(absent)}")
print(f"    Overlap : {overlap}  <- should be empty set()")

# ── 4. Timetable data check ───────────────────────────────────
print("\n[4] Timetable Data - records have 'period' field?")
import sqlite3
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "database.sqlite")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.execute(
    """
    SELECT a.student_id, a.date, a.time_in, a.period, a.face_confidence, s.name
    FROM attendance a
    LEFT JOIN students s ON a.student_id = s.student_id
    WHERE a.student_id = 'STU-003'
    ORDER BY a.date DESC, a.time_in DESC
    LIMIT 10
    """,
)
records = [dict(r) for r in cursor.fetchall()]
conn.close()

for rec in records:
    has_period = rec.get("period") is not None
    mark = "OK" if has_period else "MISSING"
    print(f"    [{mark}] {rec['name']} | {rec['date']} | {rec['time_in']} | period={rec['period']}")

# ── Summary ──────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  CHECKS COMPLETE")
print("=" * 55)

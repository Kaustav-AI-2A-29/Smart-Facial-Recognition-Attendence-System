"""
backfill_db.py — Sync missing CSV attendance records into the SQLite database.
Run once: python backfill_db.py
"""

import sys, os, csv
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database import db
from backend.attendance_service import get_period_from_time

PROJECT_ROOT  = os.path.dirname(os.path.abspath(__file__))
CSV_PATH      = os.path.join(PROJECT_ROOT, "attendance_system.csv")

# ── Map lowercase name → student_id ─────────────────────────────────────────
students = db.execute("SELECT student_id, name FROM students")
name_to_id = {row["name"].lower(): row["student_id"] for row in students}
print("[INFO] Registered students:", name_to_id)

# ── Read every CSV row and attempt to insert into DB ────────────────────────
inserted = 0
skipped  = 0

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        name       = row.get("Name", "").strip().lower()
        time_in    = row.get("Time (HH:MM:SS)", "").strip()
        date_str   = row.get("Date (YYYY-MM-DD)", "").strip()
        conf_raw   = row.get("Confidence", "0").replace("%", "").strip()
        screenshot = row.get("Screenshot", "").strip()

        if not name or not date_str or not time_in:
            continue

        student_id = name_to_id.get(name)
        if not student_id:
            print(f"[WARN] No student_id for name='{name}' — skipping")
            continue

        try:
            conf = float(conf_raw)
        except ValueError:
            conf = 0.0

        period = get_period_from_time(time_in)

        # Check if this (student, date, period) already exists
        existing = db.execute_one(
            "SELECT id FROM attendance WHERE student_id = ? AND date = ? AND period IS ?",
            (student_id, date_str, period),
        )
        if existing:
            print(f"[SKIP] {name} | {date_str} | P{period} | {time_in} — already in DB (id={existing['id']})")
            skipped += 1
            continue

        row_id = db.execute_insert(
            """
            INSERT INTO attendance
                (student_id, date, time_in, period, screenshot_path,
                 face_confidence, liveness_passed, marked_by)
            VALUES (?, ?, ?, ?, ?, ?, 1, 'system')
            """,
            (student_id, date_str, time_in, period, screenshot, conf),
        )
        print(f"[INSERT] {name} | {date_str} | P{period} | {time_in} | conf={conf:.1f}% -> rowid={row_id}")
        inserted += 1

print(f"\n{'='*50}")
print(f"  BACKFILL COMPLETE: {inserted} inserted, {skipped} skipped")
print(f"{'='*50}\n")

# ── Verify final state ───────────────────────────────────────────────────────
print("=== ALL ATTENDANCE RECORDS (DB) ===")
rows = db.execute(
    """
    SELECT a.student_id, s.name, a.date, a.time_in, a.period, a.face_confidence
    FROM attendance a
    LEFT JOIN students s ON a.student_id = s.student_id
    ORDER BY a.date DESC, a.time_in ASC
    """
)
for r in rows:
    print(f"  {r['name']:<12} | {r['date']} | {r['time_in']} | P{r['period']} | {r['face_confidence']:.1f}%")

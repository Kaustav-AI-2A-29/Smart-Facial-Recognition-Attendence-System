"""
test_csv_faculty.py — Verify Faculty Dashboard CSV helpers return correct data.
"""
import csv, os, sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
CSV_PATH = os.path.join(PROJECT_ROOT, "attendance_system.csv")

# ── Replicate helper functions ───────────────────────────────────────

def _load_all_csv():
    if not os.path.exists(CSV_PATH):
        return []
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    rows.reverse()
    return rows


def get_attendance_csv_by_student(student_name, limit=365):
    rows = _load_all_csv()
    seen_dates = set()
    records = []
    for row in rows:
        name = row.get("Name", "").strip().lower()
        if name != student_name.strip().lower():
            continue
        row_date = row.get("Date (YYYY-MM-DD)", "").strip()
        if row_date in seen_dates:
            continue
        seen_dates.add(row_date)
        conf_str = row.get("Confidence", "0").replace("%", "").strip()
        try:
            conf_val = float(conf_str)
        except ValueError:
            conf_val = 0.0
        records.append({
            "student_name":    student_name.title(),
            "date":            row_date,
            "time_in":         row.get("Time (HH:MM:SS)", "").strip(),
            "face_confidence": conf_val,
            "screenshot_path": row.get("Screenshot", "").strip(),
        })
        if len(records) >= limit:
            break
    return records


def get_attendance_stats_csv(student_name, start_date, end_date):
    rows = _load_all_csv()
    present_dates = set()
    for row in rows:
        name = row.get("Name", "").strip().lower()
        if name != student_name.strip().lower():
            continue
        d = row.get("Date (YYYY-MM-DD)", "").strip()
        if start_date <= d <= end_date:
            present_dates.add(d)
    from datetime import date as date_cls
    start = date_cls.fromisoformat(start_date)
    end   = date_cls.fromisoformat(end_date)
    total_days = (end - start).days + 1
    present    = len(present_dates)
    absent     = total_days - present
    percentage = round((present / total_days) * 100, 1) if total_days > 0 else 0.0
    return {"total_days": total_days, "present": present, "absent": absent, "percentage": percentage}


# ── Run tests ────────────────────────────────────────────────────────
print("=" * 55)
print("  Faculty Dashboard CSV Logic Verification")
print("=" * 55)

print(f"\nCSV file: {CSV_PATH}")
print(f"Exists:   {os.path.exists(CSV_PATH)}\n")

print("[1] Raw CSV contents:")
all_rows = _load_all_csv()
for r in all_rows:
    print(f"  Name={r.get('Name')!r} | Date={r.get('Date (YYYY-MM-DD)')!r} | "
          f"Time={r.get('Time (HH:MM:SS)')!r} | Conf={r.get('Confidence')!r}")

print("\n[2] get_attendance_csv_by_student('kaustav'):")
records = get_attendance_csv_by_student("kaustav")
if records:
    for rec in records:
        shot_exists = os.path.exists(rec["screenshot_path"]) if rec["screenshot_path"] else False
        print(f"  date={rec['date']} | time={rec['time_in']} | "
              f"conf={rec['face_confidence']}% | screenshot_exists={shot_exists}")
else:
    print("  No records found!")

from datetime import date
today       = date.today().isoformat()
start_month = date.today().replace(day=1).isoformat()

print(f"\n[3] get_attendance_stats_csv('kaustav', {start_month!r}, {today!r}):")
stats = get_attendance_stats_csv("kaustav", start_month, today)
print(f"  present={stats['present']} | absent={stats['absent']} | "
      f"total={stats['total_days']} | pct={stats['percentage']}%")

print("\n" + "=" * 55)
print("  All checks complete")
print("=" * 55)

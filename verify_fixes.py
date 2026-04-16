"""verify_fixes.py — Quick sanity check for all three fixes."""
import csv, os, sqlite3

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

print("=== Verifying all fixes ===\n")

# 1. attendance_system.csv
print("[1] attendance_system.csv:")
csv_path = os.path.join(PROJECT_ROOT, "attendance_system.csv")
if os.path.exists(csv_path):
    with open(csv_path, newline="") as f:
        for i, row in enumerate(csv.reader(f)):
            print(f"   Row {i}: {row}")
else:
    print("   File not found!")
print()

# 2. DB screenshot paths
print("[2] DB screenshot paths (absolute & file exists):")
db_path = os.path.join(PROJECT_ROOT, "data", "database.sqlite")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT student_id, time_in, screenshot_path FROM attendance ORDER BY id")
rows = cur.fetchall()
conn.close()
if rows:
    for r in rows:
        p = r["screenshot_path"] or ""
        exists = os.path.exists(p) if p else False
        abs_flag = os.path.isabs(p) if p else False
        print(f"   {r['student_id']} | {r['time_in']} | abs={abs_flag} | exists={exists}")
        if p:
            print(f"     path: {p}")
else:
    print("   No records in DB.")
print()

# 3. resolve_screenshot_path logic
print("[3] resolve_screenshot_path (handles both abs & relative):")

def resolve(screenshot_path):
    if not screenshot_path:
        return ""
    if os.path.isabs(screenshot_path) and os.path.exists(screenshot_path):
        return screenshot_path
    candidate = os.path.join(PROJECT_ROOT, screenshot_path)
    return candidate if os.path.exists(candidate) else ""

test_cases = [
    os.path.join(PROJECT_ROOT, "screenshots", "Kaustav_20260416_035432.jpg"),
    "screenshots/Kaustav_20260416_035432.jpg",
    "",
]
for p in test_cases:
    result = resolve(p)
    label = "..." + p[-40:] if len(p) > 40 else (p if p else "(empty)")
    print(f"   {label!r:50s} -> resolved={bool(result)}")

print("\n=== All checks complete ===")

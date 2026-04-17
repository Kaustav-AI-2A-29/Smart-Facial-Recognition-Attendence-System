"""
02_Faculty_Dashboard.py — Faculty admin: student list, detail view, attendance.
Attendance data is read from attendance_system.csv (live), not the SQLite DB.
"""

import sys
import os
import csv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from dotenv import load_dotenv
from datetime import date, datetime
import pandas as pd

load_dotenv()

from backend.student_service import get_all_students, get_student_by_id, delete_student
from backend.attendance_service import mark_attendance_manual
from backend.image_processor import get_profile_picture_path
from frontend.components.sidebar import render_sidebar
from frontend.components.attendance_table import render_attendance_table
from frontend.components.student_list import render_student_list

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CSV_PATH     = os.path.join(PROJECT_ROOT, "attendance_system.csv")


# ── Screenshot helper ──────────────────────────────────────────────────────────

def resolve_screenshot(path: str) -> str:
    """Return absolute path if the screenshot file exists, else empty string."""
    if not path:
        return ""
    if os.path.isabs(path) and os.path.exists(path):
        return path
    candidate = os.path.join(PROJECT_ROOT, path)
    return candidate if os.path.exists(candidate) else ""


# ── Card renderer (uses st.image — works with local paths) ────────────────────

def render_student_attendance_cards(records: list) -> None:
    """Render attendance records as cards with st.image() for screenshots."""
    if not records:
        st.info("No attendance records found.")
        return
    for rec in records:
        col_info, col_img = st.columns([2, 1])
        with col_info:
            st.markdown(f"**📅 Date:** {rec['date']}")
            st.markdown(f"**⏰ Time In:** {rec['time_in']}")
            conf = rec.get("face_confidence", 0)
            st.markdown(f"**🎯 Confidence:** {conf:.1f}%")
        with col_img:
            resolved = resolve_screenshot(rec.get("screenshot_path", ""))
            if resolved:
                try:
                    st.image(resolved, width=180, caption="Captured face")
                except Exception as e:
                    st.warning(f"Image error: {e}")
            else:
                st.caption("No screenshot")
        st.divider()


# ── CSV helpers ────────────────────────────────────────────────────────────────

def _load_all_csv() -> list:
    """Read every row from attendance_system.csv, reversed so newest is first."""
    if not os.path.exists(CSV_PATH):
        return []
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    rows.reverse()
    return rows


def get_attendance_csv_by_student(student_name: str, limit: int = 365) -> list:
    """Return attendance records for a student from CSV, shaped like DB records.
    Deduplicates by date — keeps the latest time entry per date.
    """
    rows = _load_all_csv()
    seen_dates = set()
    records = []
    for row in rows:
        name = row.get("Name", "").strip().lower()
        if name != student_name.strip().lower():
            continue
        row_date = row.get("Date (YYYY-MM-DD)", "").strip()
        if row_date in seen_dates:
            continue          # keep only latest per date (rows are newest-first)
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


def get_attendance_stats_csv(student_name: str, start_date: str, end_date: str) -> dict:
    """Compute present/absent/percentage from CSV for a date range."""
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
    start      = date_cls.fromisoformat(start_date)
    end        = date_cls.fromisoformat(end_date)
    total_days = (end - start).days + 1
    present    = len(present_dates)
    absent     = total_days - present
    percentage = round((present / total_days) * 100, 1) if total_days > 0 else 0.0
    return {"total_days": total_days, "present": present,
            "absent": absent, "percentage": percentage}


def get_all_attendance_csv() -> list:
    """All records from CSV, deduped by (name, date), for the recent logs section."""
    rows = _load_all_csv()
    seen = set()
    records = []
    for row in rows:
        name     = row.get("Name", "").strip()
        row_date = row.get("Date (YYYY-MM-DD)", "").strip()
        key = (name.lower(), row_date)
        if key in seen:
            continue
        seen.add(key)
        conf_str = row.get("Confidence", "0").replace("%", "").strip()
        try:
            conf_val = float(conf_str)
        except ValueError:
            conf_val = 0.0
        records.append({
            "student_name":    name.title(),
            "date":            row_date,
            "time_in":         row.get("Time (HH:MM:SS)", "").strip(),
            "face_confidence": conf_val,
            "screenshot_path": row.get("Screenshot", "").strip(),
        })
    return records


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Faculty Dashboard", page_icon="👩‍🏫", layout="wide")

for key, default in {
    "logged_in": False, "role": None,
    "selected_student_id": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

render_sidebar()

if not st.session_state.logged_in or st.session_state.role != "faculty":
    st.error("🚫 Access denied. Please log in as faculty.")
    st.stop()

st.title("👩‍🏫 Faculty Dashboard")

# ── Detail view ────────────────────────────────────────────────────────────────
if st.session_state.selected_student_id:
    sid     = st.session_state.selected_student_id
    student = get_student_by_id(sid)

    if st.button("← Back to All Students"):
        st.session_state.selected_student_id = None
        st.rerun()

    if not student:
        st.error("Student not found.")
        st.stop()

    col_pic, col_info = st.columns([1, 3])
    pic_path = get_profile_picture_path(sid)
    with col_pic:
        if pic_path:
            st.image(pic_path, width=160)
        else:
            st.markdown("🧑 *No photo*")

    with col_info:
        st.subheader(student.get("name", "—"))
        for label, key in [
            ("Student ID", "student_id"), ("Roll Number", "roll_number"),
            ("Department", "department"), ("Email", "email"),
            ("Age", "age"), ("Address", "address"), ("Hobbies", "hobbies"),
        ]:
            st.markdown(f"**{label}:** {student.get(key) or '—'}")

    st.divider()

    student_name = student.get("name", "")
    today        = date.today()
    start_month  = today.replace(day=1)

    # ── Attendance Timetable ───────────────────────────────────────────────────
    from datetime import timedelta
    from frontend.components.attendance_table import render_timetable
    from backend.attendance_service import get_attendance_by_student

    if "faculty_week_offset" not in st.session_state:
        st.session_state.faculty_week_offset = 0

    st.markdown("#### 📅 Attendance Timetable")

    current_monday = date.today() - timedelta(days=date.today().weekday())
    display_monday = current_monday + timedelta(
        weeks=st.session_state.faculty_week_offset
    )

    fn1, fn2, fn3 = st.columns([1, 3, 1])
    with fn1:
        if st.button("← Prev", key="fac_prev"):
            st.session_state.faculty_week_offset -= 1
            st.rerun()
    with fn2:
        week_end = display_monday + timedelta(days=4)
        st.markdown(
            f"<div style='text-align:center'>"
            f"{display_monday.strftime('%d %b')} – {week_end.strftime('%d %b %Y')}"
            f"</div>",
            unsafe_allow_html=True,
        )
    with fn3:
        if st.button("Next →", key="fac_next"):
            st.session_state.faculty_week_offset += 1
            st.rerun()

    att_records = get_attendance_by_student(student["student_id"], limit=400)
    render_timetable(att_records, week_start=display_monday)

    if att_records:
        df = pd.DataFrame(att_records)
        available_cols = [c for c in
            ["student_id", "date", "period", "time_in", "face_confidence"]
            if c in df.columns]
        st.download_button(
            "⬇️ Export CSV",
            data=df[available_cols].to_csv(index=False).encode(),
            file_name=f"{sid}_attendance.csv",
            mime="text/csv",
        )

    st.divider()
    st.markdown("##### Actions")
    col_manual, col_delete = st.columns(2)
    if col_manual.button("✅ Mark Present Today (Manual)"):
        mark_attendance_manual(sid, marked_by=st.session_state.get("username", "faculty"))
        st.success("Attendance manually marked.")
        st.rerun()

    with col_delete.expander("⚠️ Delete Student"):
        if st.button("Confirm Delete", type="primary"):
            delete_student(sid)
            st.session_state.selected_student_id = None
            st.success(f"Student {sid} deleted.")
            st.rerun()

    st.stop()

# ── Student list ───────────────────────────────────────────────────────────────
st.markdown("#### 🗂 All Students")
all_students = get_all_students()
if not all_students:
    st.info("No students found. Run `seed_data.py` to add test data.")
else:
    selected = render_student_list(all_students)
    if selected:
        st.session_state.selected_student_id = selected["student_id"]
        st.rerun()

st.divider()

# ── Recent Attendance Logs ─────────────────────────────────────────────────────
st.markdown("#### 📸 Recent Attendance Logs")
st.caption(f"Live from `attendance_system.csv` — {datetime.now().strftime('%H:%M:%S')}")
all_attendance = get_all_attendance_csv()
if not all_attendance:
    st.info("No attendance records found.")
else:
    render_attendance_table(all_attendance, show_screenshot=True, show_confidence=True)

st.divider()

# Full data export
if all_students:
    df_all = pd.DataFrame(all_students).drop(
        columns=["profile_picture_path", "id"], errors="ignore"
    )
    st.download_button(
        "⬇️ Download All Student Data (CSV)",
        data=df_all.to_csv(index=False).encode(),
        file_name="all_students.csv",
        mime="text/csv",
    )

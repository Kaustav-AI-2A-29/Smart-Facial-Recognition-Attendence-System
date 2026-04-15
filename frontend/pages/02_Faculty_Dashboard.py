"""
02_Faculty_Dashboard.py — Faculty admin: student list, detail view, attendance.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from backend.student_service import get_all_students, search_students, delete_student
from backend.attendance_service import (
    get_attendance_by_student,
    get_attendance_stats,
    mark_attendance_manual,
)
from backend.image_processor import get_profile_picture_path
from frontend.components.sidebar import render_sidebar
from frontend.components.attendance_table import render_attendance_table
from frontend.components.student_list import render_student_list

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

# ── Detail view mode ───────────────────────────────────────────────────
if st.session_state.selected_student_id:
    sid = st.session_state.selected_student_id
    from backend.student_service import get_student_by_id

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

    # Attendance tabs
    from datetime import date

    tab_month, tab_all = st.tabs(["📅 This Month", "📂 All Time"])
    today = date.today()
    start_month = today.replace(day=1)

    with tab_month:
        stats = get_attendance_stats(sid, start_month.isoformat(), today.isoformat())
        c1, c2, c3 = st.columns(3)
        c1.metric("✅ Present", stats["present"])
        c2.metric("❌ Absent", stats["absent"])
        c3.metric("📊 Attendance", f"{stats['percentage']}%")
        records = get_attendance_by_student(sid, limit=31)
        render_attendance_table(records, show_confidence=True)

    with tab_all:
        all_records = get_attendance_by_student(sid, limit=365)
        render_attendance_table(all_records, show_confidence=True)
        if all_records:
            import pandas as pd

            df = pd.DataFrame(all_records)[["student_id", "date", "time_in", "face_confidence"]]
            st.download_button(
                "⬇️ Export CSV",
                data=df.to_csv(index=False).encode(),
                file_name=f"{sid}_attendance.csv",
                mime="text/csv",
            )

    st.divider()
    st.markdown("##### Actions")
    col_manual, col_delete = st.columns(2)
    if col_manual.button("✅ Mark Present Today (Manual)"):
        mark_attendance_manual(sid, marked_by=st.session_state.username)
        st.success("Attendance manually marked.")
        st.rerun()

    with col_delete.expander("⚠️ Delete Student"):
        if st.button("Confirm Delete", type="primary"):
            delete_student(sid)
            st.session_state.selected_student_id = None
            st.success(f"Student {sid} deleted.")
            st.rerun()

    st.stop()

# ── Student list view ──────────────────────────────────────────────────
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

# Full data export
import pandas as pd

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

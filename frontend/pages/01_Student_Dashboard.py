"""
01_Student_Dashboard.py — Student profile view/edit + attendance history.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from backend.student_service import get_student_by_user_id
from backend.attendance_service import get_attendance_by_student, get_attendance_stats
from backend.image_processor import get_profile_picture_path
from frontend.components.sidebar import render_sidebar
from frontend.components.attendance_table import render_attendance_table
from frontend.components.student_profile_form import render_profile_form

st.set_page_config(page_title="Student Dashboard", page_icon="🎒", layout="wide")

for key, default in {
    "logged_in": False, "role": None, "user_id": None,
    "student_id": None, "name": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

render_sidebar()

if not st.session_state.logged_in or st.session_state.role != "student":
    st.error("🚫 Access denied. Please log in as a student.")
    st.stop()

student = get_student_by_user_id(st.session_state.user_id)
if student is None:
    st.error("⚠️ Student profile not found. Contact your administrator.")
    st.stop()

st.title(f"🎒 Dashboard — {student['name']}")
st.caption(f"Student ID: **{student['student_id']}**")

# ── Profile section ────────────────────────────────────────────────────
tab_profile, tab_attendance = st.tabs(["👤 My Profile", "📅 My Attendance"])

with tab_profile:
    col_pic, col_info = st.columns([1, 3])

    pic_path = get_profile_picture_path(student["student_id"])
    with col_pic:
        if pic_path:
            st.image(pic_path, width=160, caption="Profile Picture")
        else:
            st.markdown(
                "<div style='width:160px;height:160px;background:#e0e7ef;"
                "border-radius:50%;display:flex;align-items:center;"
                "justify-content:center;font-size:3rem;'>🧑</div>",
                unsafe_allow_html=True,
            )

    with col_info:
        info = {
            "Name": student.get("name", "—"),
            "Age": student.get("age", "—"),
            "Roll Number": student.get("roll_number", "—"),
            "Department": student.get("department", "—"),
            "Email": student.get("email", "—"),
            "Address": student.get("address", "—"),
            "Hobbies": student.get("hobbies", "—"),
        }
        for label, val in info.items():
            st.markdown(f"**{label}:** {val or '—'}")

    st.divider()

    with st.expander("✏️ Edit Profile", expanded=False):
        render_profile_form(student)


with tab_attendance:
    from datetime import date, timedelta

    today = date.today()
    start_of_month = today.replace(day=1)
    stats = get_attendance_stats(
        student["student_id"],
        start_of_month.isoformat(),
        today.isoformat(),
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Present", stats["present"])
    col2.metric("❌ Absent", stats["absent"])
    col3.metric("📊 This Month", f"{stats['percentage']}%")

    st.markdown("#### Attendance History (last 30 records)")
    records = get_attendance_by_student(student["student_id"], limit=30)
    render_attendance_table(records, show_screenshot=True)

    if records:
        import pandas as pd
        df_export = pd.DataFrame(records)[["student_id", "date", "time_in", "face_confidence"]]
        csv = df_export.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download Report (CSV)",
            data=csv,
            file_name=f"{student['student_id']}_attendance.csv",
            mime="text/csv",
        )

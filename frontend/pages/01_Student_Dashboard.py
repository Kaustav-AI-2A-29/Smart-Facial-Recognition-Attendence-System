"""
01_Student_Dashboard.py — Student profile view/edit + attendance history.
REAL-TIME DATA FETCHING - No caching, guaranteed fresh data.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

from backend.student_service import get_student_by_user_id
from frontend.realtime_data import (
    load_fresh_attendance_data,
    load_fresh_attendance_stats,
    get_database_timestamp,
    get_latest_attendance_record,
    verify_fresh_data
)
from backend.image_processor import get_profile_picture_path
from frontend.components.sidebar import render_sidebar
from frontend.components.attendance_table import render_attendance_table, render_timetable
from frontend.components.student_profile_form import render_profile_form

st.set_page_config(page_title="Student Dashboard", page_icon="🎒", layout="wide")

for key, default in {
    "logged_in": False, "role": None, "user_id": None,
    "student_id": None, "name": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if "week_offset" not in st.session_state:
    st.session_state.week_offset = 0

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

    # ── Refresh controls ──────────────────────────────────────────
    col_ts, col_refresh = st.columns([3, 1])
    with col_ts:
        st.info(f"⏱️ **Last Refreshed:** {get_database_timestamp()}")
    with col_refresh:
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    # ── Monthly stats ─────────────────────────────────────────────
    today = date.today()
    start_of_month = today.replace(day=1)
    stats = load_fresh_attendance_stats(
        student["student_id"],
        start_of_month.isoformat(),
        today.isoformat(),
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Periods Present (Month)", stats["present"])
    col2.metric("❌ Periods Absent (Month)",  stats["absent"])
    col3.metric("📊 Attendance %",            f"{stats['percentage']}%")

    st.divider()

    # ── Week navigation ───────────────────────────────────────────
    st.markdown("#### 📅 Weekly Timetable")

    # Compute the Monday of the current displayed week
    current_monday = today - timedelta(days=today.weekday())
    display_monday = current_monday + timedelta(
        weeks=st.session_state.week_offset
    )

    nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
    with nav_col1:
        if st.button("← Prev Week"):
            st.session_state.week_offset -= 1
            st.rerun()
    with nav_col2:
        week_end = display_monday + timedelta(days=4)
        st.markdown(
            f"<div style='text-align:center;font-weight:500'>"
            f"{display_monday.strftime('%d %b')} – {week_end.strftime('%d %b %Y')}"
            f"</div>",
            unsafe_allow_html=True,
        )
    with nav_col3:
        if st.button("Next Week →"):
            st.session_state.week_offset += 1
            st.rerun()

    if st.session_state.week_offset != 0:
        if st.button("📍 Back to current week"):
            st.session_state.week_offset = 0
            st.rerun()

    st.markdown("")  # spacing

    # ── Load records and render timetable ─────────────────────────
    records_df = load_fresh_attendance_data(student["student_id"], limit=200)
    records = records_df.to_dict("records") if not records_df.empty else []
    st.success(f"✅ {len(records)} total period record(s) on file")

    render_timetable(records, week_start=display_monday)

    # ── CSV export ────────────────────────────────────────────────
    if records:
        import pandas as pd
        df_export = pd.DataFrame(records)
        available_cols = [c for c in
            ["student_id", "date", "period", "time_in", "face_confidence"]
            if c in df_export.columns]
        csv = df_export[available_cols].to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download Full Report (CSV)",
            data=csv,
            file_name=f"{student['student_id']}_attendance.csv",
            mime="text/csv",
        )

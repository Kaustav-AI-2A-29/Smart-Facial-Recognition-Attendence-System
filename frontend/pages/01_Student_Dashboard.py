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
    
    # STEP 1: Display refresh timestamp - proves fresh loads
    col_timestamp, col_refresh = st.columns([3, 1])
    with col_timestamp:
        current_time = get_database_timestamp()
        st.info(f"⏱️ **Last Refreshed:** {current_time} (Data is guaranteed fresh)")
    
    with col_refresh:
        if st.button("🔄 Refresh Now", use_container_width=True):
            # Clear caches before rerun
            st.cache_data.clear()
            st.rerun()

    st.divider()

    # STEP 2: Load attendance statistics with fresh connection
    today = date.today()
    start_of_month = today.replace(day=1)
    
    stats = load_fresh_attendance_stats(
        student["student_id"],
        start_of_month.isoformat(),
        today.isoformat(),
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Present", stats["present"])
    col2.metric("❌ Absent", stats["absent"])
    col3.metric("📊 This Month", f"{stats['percentage']}%")

    st.markdown("#### 📋 Attendance History (Fresh Data)")
    
    # STEP 3: Load attendance with guaranteed fresh connection
    records_df = load_fresh_attendance_data(student["student_id"], limit=30)
    
    # Convert DataFrame to list of dicts for display
    records = records_df.to_dict('records') if not records_df.empty else []
    
    # STEP 4: Show debug info and latest record
    st.success(f"✅ Retrieved {len(records)} record(s) from database")
    
    if records:
        # Show latest record details
        latest = records[0]
        st.info(
            f"📍 **Latest:** {latest.get('date')} at {latest.get('time_in')} "
            f"→ Confidence: **{latest.get('face_confidence', 0):.1f}%**"
        )
    
    # STEP 5: Display raw data table
    if not records_df.empty:
        st.warning("🔍 **Raw Database Output (Debug View):**")
        # Select key columns for display
        display_cols = ['date', 'time_in', 'face_confidence', 'student_name', 'screenshot_path']
        display_cols = [col for col in display_cols if col in records_df.columns]
        st.dataframe(records_df[display_cols], use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No attendance records yet. Start marking attendance to see data here.")
    
    # STEP 6: Display formatted attendance table
    st.divider()
    st.markdown("#### 📅 Formatted Attendance Table")
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

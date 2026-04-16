"""
04_Attendance_Records.py — View real-time attendance records with screenshots.
Faculty-only view of today's attendance with face recognition results.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from datetime import date
import time

load_dotenv()

from backend.database import db
from frontend.components.sidebar import render_sidebar

st.set_page_config(
    page_title="Attendance Records",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Disable all caching to ensure fresh data
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = 0

for key, default in {"logged_in": False, "role": None}.items():
    if key not in st.session_state:
        st.session_state[key] = default

render_sidebar()

if not st.session_state.logged_in or st.session_state.role != "faculty":
    st.error("🚫 Access denied. Faculty login required.")
    st.stop()

st.title("📊 Attendance Records")
st.caption("View recorded attendance with screenshots and timestamps")

# ─────────────────────────────────────────────────────────────
# Auto-refresh: Rerun every 5 seconds to check for new data
# ─────────────────────────────────────────────────────────────
placeholder_refresh = st.empty()
if placeholder_refresh.button("🔄 Refresh Now", key="refresh_btn"):
    st.rerun()

# Auto-refresh interval
refresh_interval = 5  # seconds
current_time = time.time()
if current_time - st.session_state.last_refresh > refresh_interval:
    st.session_state.last_refresh = current_time
    st.rerun()

# Get filter options
tab_today, tab_custom = st.tabs(["📅 Today", "🔍 Custom Date Range"])

with tab_today:
    today_str = date.today().isoformat()
    
    # Query attendance for today - FORCE FRESH READ (no caching)
    rows = db.execute(
        """
        SELECT a.*, s.name as student_name, u.username
        FROM attendance a
        LEFT JOIN students s ON a.student_id = s.student_id
        LEFT JOIN users u ON s.user_id = u.id
        WHERE a.date = ?
        ORDER BY a.time_in DESC
        """,
        (today_str,)
    )
    
    records = [dict(r) for r in rows]
    
    if not records:
        st.info("ℹ️ No attendance records for today yet.")
    else:
        # Calculate present and absent counts
        total_students = 4  # Number of students in the system
        present_count = len(records)
        absent_count = total_students - present_count
        
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ Present", present_count)
        col2.metric("❌ Absent", absent_count)
        col3.metric("📊 Attendance %", f"{(present_count/total_students)*100:.0f}%")
        
        st.divider()
        
        # Display attendance records with screenshots
        for record in records:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(f"👤 {record['student_name'] or 'Unknown'}")
                col_time, col_id = st.columns(2)
                col_time.write(f"⏰ **Time:** {record['time_in']}")
                col_id.write(f"📍 **ID:** {record['student_id']}")
                
                # Display confidence as percentage
                if record['face_confidence'] is not None and record['face_confidence'] > 0:
                    st.write(f"🎯 **Confidence:** {record['face_confidence']:.1f}%")
                else:
                    st.write(f"🎯 **Confidence:** N/A")
            
            with col2:
                # Display screenshot if available
                if record['screenshot_path'] and os.path.exists(record['screenshot_path']):
                    try:
                        st.image(record['screenshot_path'], width=200, caption="Captured face")
                    except Exception as e:
                        st.warning(f"Could not load image: {e}")
                else:
                    st.warning("No screenshot available")
            
            st.divider()


with tab_custom:
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date", value=date.today())
    end_date = col2.date_input("End Date", value=date.today())
    
    if st.button("🔍 Search"):
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        
        rows = db.execute(
            """
            SELECT a.*, s.name as student_name, u.username
            FROM attendance a
            LEFT JOIN students s ON a.student_id = s.student_id
            LEFT JOIN users u ON s.user_id = u.id
            WHERE a.date BETWEEN ? AND ?
            ORDER BY a.date DESC, a.time_in DESC
            """,
            (start_str, end_str)
        )
        
        records = [dict(r) for r in rows]
        
        if not records:
            st.info("No attendance records in this date range.")
        else:
            st.success(f"✅ **Found {len(records)} record(s)**")
            
            # Show as table
            df = pd.DataFrame(records)[['student_name', 'date', 'time_in', 'face_confidence']]
            df.columns = ['Student', 'Date', 'Time', 'Confidence']
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download as CSV",
                csv,
                f"attendance_{start_str}_to_{end_str}.csv",
                "text/csv"
            )

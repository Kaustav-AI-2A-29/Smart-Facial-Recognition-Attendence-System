"""
04_Attendance_Records.py — View real-time attendance records with screenshots.
Reads directly from attendance_system.csv — updated on every recognition event.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import csv
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from datetime import date, datetime
import time

load_dotenv()

from backend.database import db
from frontend.components.sidebar import render_sidebar

# ── Project paths ──────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CSV_PATH = os.path.join(PROJECT_ROOT, "attendance_system.csv")


def resolve_screenshot(path: str) -> str:
    """Return an absolute path if the screenshot file exists, else empty string."""
    if not path:
        return ""
    if os.path.isabs(path) and os.path.exists(path):
        return path
    candidate = os.path.join(PROJECT_ROOT, path)
    return candidate if os.path.exists(candidate) else ""


def load_csv_records(date_filter: str = None, start_date: str = None, end_date: str = None):
    """
    Read attendance_system.csv and return a list of record dicts.
    Optionally filter by exact date or a date range (YYYY-MM-DD strings).
    Deduplicates by name+date so each student appears once (latest entry wins).
    """
    records = []
    if not os.path.exists(CSV_PATH):
        return records

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_date = row.get("Date (YYYY-MM-DD)", "").strip()
            if date_filter and row_date != date_filter:
                continue
            if start_date and end_date:
                if not (start_date <= row_date <= end_date):
                    continue
            records.append({
                "name":        row.get("Name", "").strip().title(),
                "time_in":     row.get("Time (HH:MM:SS)", "").strip(),
                "date":        row_date,
                "confidence":  row.get("Confidence", "").strip(),
                "screenshot":  row.get("Screenshot", "").strip(),
            })

    # Deduplicate — keep the *latest* entry per student per date
    seen = {}
    for rec in records:
        key = (rec["name"].lower(), rec["date"])
        # later rows (appended later) overwrite earlier ones
        seen[key] = rec
    return list(seen.values())


def get_student_id(name: str) -> str:
    """Look up student_id from DB by name (case-insensitive)."""
    result = db.execute_one(
        "SELECT student_id FROM students WHERE LOWER(name) = LOWER(?)", (name,)
    )
    return result["student_id"] if result else "—"


def get_known_names() -> list:
    """All student names registered in the DB."""
    rows = db.execute("SELECT name FROM students ORDER BY name")
    return [r["name"].title() for r in rows]

# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Attendance Records",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

for key, default in {"logged_in": False, "role": None}.items():
    if key not in st.session_state:
        st.session_state[key] = default

render_sidebar()

if not st.session_state.logged_in or st.session_state.role != "faculty":
    st.error("🚫 Access denied. Faculty login required.")
    st.stop()

st.title("📊 Attendance Records")
st.caption(f"Live data from `attendance_system.csv` — refreshes every 5 s")

# ── Auto-refresh ─────────────────────────────────────────────────────
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = 0

col_btn, col_ts = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Refresh Now", key="refresh_btn"):
        st.rerun()
with col_ts:
    st.caption(f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}")

if time.time() - st.session_state.last_refresh > 5:
    st.session_state.last_refresh = time.time()
    st.rerun()

# ── Tabs ──────────────────────────────────────────────────────────────
tab_today, tab_custom = st.tabs(["📅 Today", "🔍 Custom Date Range"])

# ════════════════════════════════════════════════════════════
# TODAY TAB
# ════════════════════════════════════════════════════════════
with tab_today:
    today_str = date.today().isoformat()
    records = load_csv_records(date_filter=today_str)
    known_names = get_known_names()

    total_students = len(known_names) if known_names else 4
    present_names  = {r["name"] for r in records}
    present_count  = len(present_names)
    absent_count   = total_students - present_count
    pct            = f"{(present_count / total_students) * 100:.0f}%" if total_students else "0%"

    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Present", present_count)
    col2.metric("❌ Absent",  absent_count)
    col3.metric("📊 Attendance %", pct)

    st.divider()

    if not records:
        st.info("ℹ️ No attendance records for today yet.")
    else:
        for rec in sorted(records, key=lambda r: r["time_in"], reverse=True):
            col_info, col_img = st.columns([2, 1])

            sid = get_student_id(rec["name"])

            with col_info:
                st.subheader(f"👤 {rec['name']}")
                c1, c2 = st.columns(2)
                c1.write(f"⏰ **Time:** {rec['time_in']}")
                c2.write(f"📍 **ID:** {sid}")
                conf_raw = rec["confidence"].replace("%", "").strip()
                try:
                    conf_val = float(conf_raw)
                    st.write(f"🎯 **Confidence:** {conf_val:.1f}%")
                except ValueError:
                    st.write(f"🎯 **Confidence:** {rec['confidence'] or 'N/A'}")

            with col_img:
                resolved = resolve_screenshot(rec["screenshot"])
                if resolved:
                    try:
                        st.image(resolved, width=200, caption="Captured face")
                    except Exception as e:
                        st.warning(f"Could not load image: {e}")
                else:
                    st.warning("No screenshot available")

            st.divider()

    # Absent list
    if known_names:
        absent_names = [n for n in known_names if n not in present_names]
        if absent_names:
            st.markdown("#### ❌ Absent Today")
            for n in absent_names:
                st.markdown(f"- {n}")

# ════════════════════════════════════════════════════════════
# CUSTOM DATE RANGE TAB
# ════════════════════════════════════════════════════════════
with tab_custom:
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date", value=date.today())
    end_date   = col2.date_input("End Date",   value=date.today())

    if st.button("🔍 Search"):
        records = load_csv_records(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        if not records:
            st.info("No attendance records in this date range.")
        else:
            st.success(f"✅ **Found {len(records)} record(s)**")
            df = pd.DataFrame(records)[["name", "date", "time_in", "confidence"]]
            df.columns = ["Student", "Date", "Time", "Confidence"]
            st.dataframe(df, use_container_width=True, hide_index=True)

            csv_dl = df.to_csv(index=False)
            st.download_button(
                "📥 Download as CSV",
                csv_dl,
                f"attendance_{start_date.isoformat()}_to_{end_date.isoformat()}.csv",
                "text/csv",
            )

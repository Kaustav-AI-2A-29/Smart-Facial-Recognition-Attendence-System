"""
attendance_table.py — Reusable attendance table display component.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict


def render_attendance_table(
    records: List[Dict],
    show_screenshot: bool = True,
    show_confidence: bool = False,
) -> None:
    """Display attendance records in a formatted table.

    Args:
        records: List of attendance dictionaries from attendance_service.
        show_screenshot: Whether to show screenshot preview links.
        show_confidence: Whether to show face confidence column.
    """
    if not records:
        st.info("No attendance records found.")
        return

    df = pd.DataFrame(records)
    columns = ["date", "time_in"]
    rename_map = {"date": "Date", "time_in": "Time In"}

    if "student_name" in df.columns:
        columns.insert(0, "student_name")
        rename_map["student_name"] = "Student Name"

    if show_confidence and "face_confidence" in df.columns:
        # face_confidence is stored as 0-100, not as decimal
        df["face_confidence"] = df["face_confidence"].apply(
            lambda x: f"{float(x):.1f}%" if pd.notnull(x) and float(x) > 0 else "—"
        )
        columns.append("face_confidence")
        rename_map["face_confidence"] = "Confidence"

    df["status"] = df["time_in"].apply(
        lambda t: "✅ Present" if pd.notnull(t) else "❌ Absent"
    )
    columns.append("status")
    rename_map["status"] = "Status"
    
    if show_screenshot and "screenshot_path" in df.columns:
        columns.append("screenshot_path")
        rename_map["screenshot_path"] = "Screenshot"

    df = df[columns].rename(columns=rename_map)
    
    if show_screenshot and "Screenshot" in df.columns:
        st.dataframe(df, use_container_width=True, hide_index=True, column_config={
            "Screenshot": st.column_config.ImageColumn()
        })
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


import calendar  # noqa: E402  (placed here to avoid disrupting existing imports above)
from datetime import date, timedelta

PERIODS = {
    1: "09:00–10:00",
    2: "10:00–11:00",
    3: "11:00–12:00",
    4: "12:00–13:00",
    5: "13:00–14:00",
    6: "14:00–15:00",
    7: "15:00–16:00",
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def render_timetable(records: list, week_start: date) -> None:
    """Render a 5-day × 7-period attendance timetable for one week.

    Args:
        records: List of attendance dicts. Each must have 'date' (YYYY-MM-DD)
                 and 'period' (int 1-7 or None).
        week_start: The Monday of the week to display (a datetime.date object).
    """
    # Build a set of (date_str, period) tuples that are marked present
    marked = set()
    for r in records:
        if r.get("period") and r.get("date"):
            marked.add((r["date"], int(r["period"])))

    # Generate the 5 dates in the week (Mon-Fri)
    week_dates = [week_start + timedelta(days=i) for i in range(5)]
    today = date.today()

    # ── Header row ─────────────────────────────────────────────
    header_cols = st.columns([1.4] + [1] * 5)
    header_cols[0].markdown("**Period / Time**")
    for i, d in enumerate(week_dates):
        if d == today:
            header_cols[i + 1].markdown(f"**:blue[{d.strftime('%a')}]**\n{d.strftime('%d %b')}")
        else:
            header_cols[i + 1].markdown(f"**{d.strftime('%a')}**\n{d.strftime('%d %b')}")

    st.markdown("---")

    # ── One row per period ──────────────────────────────────────
    for period_num, time_label in PERIODS.items():
        row_cols = st.columns([1.4] + [1] * 5)
        row_cols[0].markdown(f"**P{period_num}** `{time_label}`")

        for i, d in enumerate(week_dates):
            date_str = d.isoformat()
            is_future = d > today
            cell_key = (date_str, period_num)

            if cell_key in marked:
                row_cols[i + 1].markdown("✅")
            elif is_future:
                row_cols[i + 1].markdown("·")
            else:
                row_cols[i + 1].markdown("—")

    st.markdown("---")

    # ── Summary row ─────────────────────────────────────────────
    summary_cols = st.columns([1.4] + [1] * 5)
    summary_cols[0].markdown("**Total**")
    for i, d in enumerate(week_dates):
        date_str = d.isoformat()
        count = sum(1 for p in range(1, 8) if (date_str, p) in marked)
        summary_cols[i + 1].markdown(f"**{count}/7**")

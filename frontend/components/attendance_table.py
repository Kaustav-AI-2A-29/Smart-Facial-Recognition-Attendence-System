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
        df["face_confidence"] = df["face_confidence"].apply(
            lambda x: f"{float(x)*100:.1f}%" if pd.notnull(x) else "—"
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

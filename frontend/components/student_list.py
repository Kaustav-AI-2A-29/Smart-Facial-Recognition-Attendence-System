"""
student_list.py — Searchable/filterable student list component for faculty.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional


def render_student_list(students: List[Dict]) -> Optional[Dict]:
    """Render a searchable, filterable student list.

    Args:
        students: List of student dicts (from student_service.get_all_students).

    Returns:
        Selected student dict if faculty clicked 'View Details', else None.
    """
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("🔍 Search by name, ID, or department", placeholder="Search...")
    with col2:
        departments = ["All"] + sorted(
            {s["department"] for s in students if s.get("department")}
        )
        dept_filter = st.selectbox("Department", departments)

    filtered = students
    if query:
        q = query.lower()
        filtered = [
            s for s in filtered
            if q in (s.get("name") or "").lower()
            or q in (s.get("student_id") or "").lower()
            or q in (s.get("department") or "").lower()
        ]
    if dept_filter != "All":
        filtered = [s for s in filtered if s.get("department") == dept_filter]

    if not filtered:
        st.info("No students match your search.")
        return None

    st.markdown(f"**{len(filtered)} student(s) found**")
    selected = None

    for student in filtered:
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
            c1.markdown(f"**{student.get('student_id', '—')}**")
            c2.markdown(student.get("name", "—"))
            c3.markdown(student.get("department", "—"))
            if c4.button("View", key=f"view_{student['student_id']}"):
                selected = student
        st.divider()

    return selected


# Fix missing Optional import
from typing import Optional

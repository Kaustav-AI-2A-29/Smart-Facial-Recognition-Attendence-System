"""
sidebar.py — Shared sidebar navigation component.
"""

import streamlit as st


def render_sidebar() -> None:
    """Render the sidebar with user info and navigation links."""
    with st.sidebar:
        if st.session_state.get("logged_in"):
            role = st.session_state.get("role", "")
            name = st.session_state.get("name", "User")
            st.markdown(f"### 👋 Welcome, {name}!")
            if role == "student":
                st.markdown(f"**Student ID:** {st.session_state.get('student_id', '')}")
            else:
                st.markdown("**🔑 Admin Access**")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        else:
            st.markdown("### Smart Attendance System")
            st.caption("Please log in to continue.")

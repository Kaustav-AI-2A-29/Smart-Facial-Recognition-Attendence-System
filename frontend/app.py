"""
app.py — Main Streamlit entry point: login & role-based routing.
Run with: streamlit run frontend/app.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from backend.auth import login_user
from frontend.components.sidebar import render_sidebar

# ── Page config with caching DISABLED ───────────────────────────────
st.set_page_config(
    page_title="Smart Attendance System",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

# FORCE NO CACHING – disable all streamlit caching
st.cache_data.clear()
st.cache_resource.clear()

# ── Session state defaults ─────────────────────────────────────────────
for key, default in {
    "logged_in": False,
    "user_id": None,
    "username": None,
    "role": None,
    "student_id": None,
    "name": "",
    "selected_role": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

render_sidebar()

# ── If already logged in, redirect ────────────────────────────────────
if st.session_state.logged_in:
    role = st.session_state.role
    if role == "student":
        st.switch_page("pages/01_Student_Dashboard.py")
    elif role == "faculty":
        st.switch_page("pages/02_Faculty_Dashboard.py")
    st.stop()

# ── Landing page ──────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .hero-title { font-size: 2.4rem; font-weight: 800; color: #1e3a5f; margin-bottom: 0.2rem; }
    .hero-sub   { font-size: 1.1rem; color: #546e7a; margin-bottom: 2rem; }
    .role-card  { border: 2px solid #e0e7ef; border-radius: 14px; padding: 1.5rem;
                  text-align: center; cursor: pointer; transition: border-color .2s; }
    .role-card:hover { border-color: #1e3a5f; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="hero-title">🎓 Smart Attendance System</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Facial recognition · Role-based access · Local & secure</p>',
    unsafe_allow_html=True,
)

# ── Role selector ─────────────────────────────────────────────────────
if st.session_state.selected_role is None:
    st.markdown("#### Select your role to continue")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎒 Student Login", use_container_width=True, type="primary"):
            st.session_state.selected_role = "student"
            st.rerun()
    with col2:
        if st.button("👩‍🏫 Faculty Login", use_container_width=True):
            st.session_state.selected_role = "faculty"
            st.rerun()
    st.stop()

# ── Login form ────────────────────────────────────────────────────────
role_label = "Student" if st.session_state.selected_role == "student" else "Faculty"
st.markdown(f"### {role_label} Login")

with st.form("login_form"):
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    col_login, col_back = st.columns(2)
    submitted = col_login.form_submit_button("🔐 Login", use_container_width=True, type="primary")
    back = col_back.form_submit_button("← Back", use_container_width=True)

if back:
    st.session_state.selected_role = None
    st.rerun()

if submitted:
    if not username.strip() or not password:
        st.error("Please fill in both fields.")
    else:
        user = login_user(username.strip(), password)
        if user is None:
            st.error("❌ Invalid username or password. Please try again.")
        elif user["role"] != st.session_state.selected_role:
            st.error(
                f"⚠️ This account is registered as **{user['role']}**, "
                f"not {st.session_state.selected_role}. Please select the correct role."
            )
        else:
            st.session_state.logged_in = True
            st.session_state.user_id = user["user_id"]
            st.session_state.username = user["username"]
            st.session_state.role = user["role"]
            st.session_state.student_id = user.get("student_id")
            st.session_state.name = user.get("name", "")
            st.rerun()

"""
student_profile_form.py — Edit profile form with validation.
"""

import sys
import os
import streamlit as st
from typing import Dict, Optional

# Allow importing backend from any working directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.student_service import update_student
from backend.image_processor import save_profile_picture, delete_profile_picture


def render_profile_form(student: Dict) -> None:
    """Render an editable profile form and handle save logic.

    Args:
        student: Student profile dictionary from student_service.
    """
    st.subheader("✏️ Edit Profile")

    with st.form("edit_profile_form"):
        name = st.text_input("Full Name *", value=student.get("name", ""))
        age = st.number_input(
            "Age", min_value=1, max_value=100,
            value=int(student.get("age") or 18)
        )
        roll_number = st.text_input("Roll Number", value=student.get("roll_number", "") or "")
        department = st.text_input("Department", value=student.get("department", "") or "")
        email = st.text_input("Email", value=student.get("email", "") or "")
        address = st.text_area("Address", value=student.get("address", "") or "")
        hobbies = st.text_input(
            "Hobbies (comma-separated)",
            value=student.get("hobbies", "") or ""
        )

        st.markdown("##### Profile Picture")
        uploaded = st.file_uploader(
            "Upload new picture (JPG/PNG)", type=["jpg", "jpeg", "png"]
        )

        col1, col2 = st.columns(2)
        submitted = col1.form_submit_button("💾 Save Changes", use_container_width=True)
        delete_pic = col2.form_submit_button("🗑️ Delete Picture", use_container_width=True)

    if submitted:
        errors = {}
        if not name.strip():
            errors["name"] = "Name is required."
        if email and "@" not in email:
            errors["email"] = "Invalid email format."

        if errors:
            for msg in errors.values():
                st.error(msg)
            return

        try:
            update_kwargs: Dict = {
                "name": name.strip(),
                "age": int(age),
                "roll_number": roll_number.strip() or None,
                "department": department.strip() or None,
                "email": email.strip() or None,
                "address": address.strip() or None,
                "hobbies": hobbies.strip() or None,
            }

            if uploaded is not None:
                pic_path = save_profile_picture(student["student_id"], uploaded)
                update_kwargs["profile_picture_path"] = pic_path

            update_student(student["student_id"], **update_kwargs)
            st.success("✅ Profile updated successfully!")
            st.rerun()
        except ValueError as exc:
            st.error(f"Validation error: {exc}")
        except Exception as exc:
            st.error(f"Failed to save: {exc}")

    if delete_pic:
        delete_profile_picture(student["student_id"])
        update_student(student["student_id"], profile_picture_path=None)
        st.success("Profile picture deleted.")
        st.rerun()

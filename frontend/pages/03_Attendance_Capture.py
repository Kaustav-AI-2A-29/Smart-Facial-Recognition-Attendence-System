"""
03_Attendance_Capture.py — Real-time webcam attendance capture (Faculty only).
Requires dlib to be installed for actual face recognition.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from frontend.components.sidebar import render_sidebar

st.set_page_config(
    page_title="Attendance Capture", page_icon="📷", layout="wide"
)

for key, default in {"logged_in": False, "role": None}.items():
    if key not in st.session_state:
        st.session_state[key] = default

render_sidebar()

if not st.session_state.logged_in or st.session_state.role != "faculty":
    st.error("🚫 Access denied. Faculty login required.")
    st.stop()

st.title("📷 Real-Time Attendance Capture")
st.caption("Multi-face recognition · Liveness detection · Auto attendance marking")

# ── dlib check ─────────────────────────────────────────────────────────
try:
    import dlib
    _dlib_ok = True
except ImportError:
    _dlib_ok = False

if not _dlib_ok:
    st.warning(
        "⚠️ **dlib is not installed.** Face recognition is disabled. "
        "Install dlib to enable live attendance capture.\n\n"
        "Once installed, this page will automatically enable the camera feed."
    )
    st.info(
        "**How to install dlib on Windows:**\n"
        "1. Install [CMake](https://cmake.org/download/) and Visual Studio Build Tools.\n"
        "2. Run: `pip install dlib`\n"
        "3. Download model files:\n"
        "   - `shape_predictor_68_face_landmarks.dat`\n"
        "   - `dlib_face_recognition_resnet_model_v1.dat`\n"
        "4. Place both `.dat` files in the project root.\n"
        "5. Restart the app."
    )
    st.stop()

# ── Load engine ────────────────────────────────────────────────────────
from backend.encoding_manager import load_all_encodings
from backend.face_recognition_engine import FaceRecognitionEngine
from backend.liveness_detector import LivenessDetector
from frontend.components.camera_widget import start_camera_feed

if "face_engine" not in st.session_state:
    with st.spinner("Loading face encodings…"):
        encodings = load_all_encodings()
        st.session_state.face_engine = FaceRecognitionEngine(encodings)
        st.session_state.liveness = LivenessDetector()

face_engine = st.session_state.face_engine
liveness = st.session_state.liveness

# ── Status ─────────────────────────────────────────────────────────────
n_enrolled = len(face_engine.known_encodings)
if n_enrolled == 0:
    st.warning(
        "⚠️ No face encodings found in the database. "
        "Add student images to `data/dataset/{StudentName}/` and run the encoding loader."
    )

col1, col2 = st.columns(2)
col1.metric("Enrolled Students", n_enrolled)
col2.metric("Camera", "OpenCV (Webcam 0)")

st.divider()

# ── Start capture ──────────────────────────────────────────────────────
if st.button("▶ Start Capture Session", type="primary", use_container_width=True):
    marked_log = []

    def on_marked(student_id: str, confidence: float):
        marked_log.append({"student_id": student_id, "confidence": f"{confidence*100:.1f}%"})

    start_camera_feed(
        face_engine=face_engine,
        liveness_detector=liveness,
        on_attendance_recorded=on_marked,
    )

    if marked_log:
        import pandas as pd

        st.success(f"Session ended. Marked {len(marked_log)} student(s).")
        st.dataframe(pd.DataFrame(marked_log), use_container_width=True, hide_index=True)

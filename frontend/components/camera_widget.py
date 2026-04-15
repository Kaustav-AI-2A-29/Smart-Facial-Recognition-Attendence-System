"""
camera_widget.py — OpenCV webcam feed component for Streamlit.
"""

import logging
import os
import threading
from typing import Optional

import cv2
import numpy as np
import streamlit as st

logger = logging.getLogger(__name__)

_capture_active = False
_cap_lock = threading.Lock()


def start_camera_feed(
    face_engine=None,
    liveness_detector=None,
    on_attendance_recorded=None,
) -> None:
    """Stream live webcam feed with face detection overlays.

    Args:
        face_engine: FaceRecognitionEngine instance or None.
        liveness_detector: LivenessDetector instance or None.
        on_attendance_recorded: Callback(student_id, confidence) on match.
    """
    from backend.image_processor import save_attendance_screenshot
    from backend.attendance_service import record_attendance

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("❌ Could not open webcam. Check camera permissions.")
        return

    frame_placeholder = st.empty()
    status_placeholder = st.empty()
    stop = st.button("⏹ Stop Capture", key="stop_capture")
    marked_today = set()

    try:
        while not stop:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Camera frame read failed.")
                break

            annotated = frame.copy()
            results = face_engine.recognize_frame(frame) if face_engine else []

            for result in results:
                x, y, w, h = result["face_location"]
                sid = result["student_id"]
                conf = result["confidence"]

                if sid and sid not in marked_today:
                    color = (0, 255, 0)  # Green
                    label = f"{sid} {conf*100:.0f}%"
                    screenshot_path = save_attendance_screenshot(sid, frame)
                    record_attendance(sid, screenshot_path, conf)
                    marked_today.add(sid)
                    if on_attendance_recorded:
                        on_attendance_recorded(sid, conf)
                elif sid:
                    color = (0, 255, 0)
                    label = f"{sid} ✓"
                else:
                    color = (0, 0, 255)  # Red
                    label = "Unknown"

                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
                cv2.putText(
                    annotated, label, (x, max(y - 10, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
                )

            frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
            status_placeholder.info(f"✅ Marked today: {len(marked_today)} student(s)")
    finally:
        cap.release()
        frame_placeholder.empty()
        status_placeholder.empty()

"""
image_processor.py — Profile picture and screenshot handling/compression.
"""

import io
import logging
import os
from datetime import datetime
from typing import Optional

import cv2
import numpy as np

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.getenv("SCREENSHOTS_DIR", os.path.join(_BASE_DIR, "data", "screenshots"))
PROFILE_PICTURES_DIR = os.getenv("PROFILE_PICTURES_DIR", os.path.join(_BASE_DIR, "data", "profile_pictures"))
SCREENSHOT_WIDTH = int(os.getenv("SCREENSHOT_WIDTH", "640"))
SCREENSHOT_QUALITY = int(os.getenv("SCREENSHOT_QUALITY", "85"))


def _ensure_dir(path: str) -> None:
    """Create directory and all parents if they don't exist."""
    os.makedirs(path, exist_ok=True)


def save_profile_picture(student_id: str, uploaded_file) -> str:
    """Save an uploaded profile picture from Streamlit file uploader.

    Resizes to max 300x300, compresses to JPEG quality 85.

    Args:
        student_id: Used as the filename base.
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        Saved file path string.
    """
    _ensure_dir(PROFILE_PICTURES_DIR)
    file_bytes = np.frombuffer(uploaded_file.read(), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode uploaded image.")

    max_dim = 300
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    path = os.path.join(PROFILE_PICTURES_DIR, f"{student_id}.jpg")
    cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    logger.info("Saved profile picture: %s", path)
    return path


def get_profile_picture_path(student_id: str) -> Optional[str]:
    """Get the filesystem path to a student's profile picture.

    Args:
        student_id: Student ID string.

    Returns:
        Path string if exists, else None.
    """
    path = os.path.join(PROFILE_PICTURES_DIR, f"{student_id}.jpg")
    return path if os.path.exists(path) else None


def delete_profile_picture(student_id: str) -> bool:
    """Delete a student's profile picture file.

    Args:
        student_id: Student ID string.

    Returns:
        True if deleted, False if file did not exist.
    """
    path = os.path.join(PROFILE_PICTURES_DIR, f"{student_id}.jpg")
    if os.path.exists(path):
        os.remove(path)
        logger.info("Deleted profile picture: %s", path)
        return True
    return False


def compress_screenshot(frame: np.ndarray, max_width: int = SCREENSHOT_WIDTH) -> bytes:
    """Compress a video frame to JPEG bytes.

    Args:
        frame: OpenCV BGR frame as numpy array.
        max_width: Resize to this maximum width (aspect ratio preserved).

    Returns:
        JPEG-encoded bytes.
    """
    h, w = frame.shape[:2]
    if w > max_width:
        scale = max_width / w
        frame = cv2.resize(frame, (max_width, int(h * scale)))

    success, buffer = cv2.imencode(
        ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, SCREENSHOT_QUALITY]
    )
    if not success:
        raise RuntimeError("Failed to encode frame as JPEG.")
    return buffer.tobytes()


def save_attendance_screenshot(student_id: str, frame: np.ndarray) -> str:
    """Save an attendance screenshot for a student.

    Args:
        student_id: Student ID used in the filename.
        frame: OpenCV BGR frame.

    Returns:
        Saved file path string.
    """
    now = datetime.now()
    date_folder = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")

    day_dir = os.path.join(SCREENSHOTS_DIR, date_folder)
    _ensure_dir(day_dir)

    filename = f"{student_id}_{time_str}.jpg"
    path = os.path.join(day_dir, filename)

    jpeg_bytes = compress_screenshot(frame)
    with open(path, "wb") as f:
        f.write(jpeg_bytes)

    logger.info("Saved attendance screenshot: %s", path)
    return path

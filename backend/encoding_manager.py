"""
encoding_manager.py — Load, save, and manage face encodings from the database.
Note: Actual dlib-based encoding generation is deferred until dlib is installed.
This module handles the storage/retrieval layer and numpy blob conversion.
"""

import io
import logging
import os
from typing import Dict, Optional

import numpy as np

from backend.database import db

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.getenv("DATASET_DIR", os.path.join(_BASE_DIR, "dataset"))


def save_encoding_to_blob(encoding: np.ndarray) -> bytes:
    """Serialize a numpy array to bytes for SQLite BLOB storage.

    Args:
        encoding: 128-dimensional face encoding (numpy array).

    Returns:
        Binary bytes representation.
    """
    buf = io.BytesIO()
    np.save(buf, encoding)
    return buf.getvalue()


def load_encoding_from_blob(blob: bytes) -> np.ndarray:
    """Deserialize a numpy array from SQLite BLOB bytes.

    Args:
        blob: Binary bytes from the database.

    Returns:
        Restored numpy array.
    """
    buf = io.BytesIO(blob)
    return np.load(buf, allow_pickle=False)


def load_all_encodings() -> Dict[str, np.ndarray]:
    """Load all face encodings from the database into memory.

    Returns:
        Dict mapping student_id → numpy encoding array.
        If a student has multiple encodings, the first is used.
    """
    rows = db.execute("SELECT student_id, encoding FROM face_encodings")
    encodings = {}
    for row in rows:
        sid = row["student_id"]
        if sid not in encodings:  # Use first encoding per student
            try:
                encodings[sid] = load_encoding_from_blob(row["encoding"])
            except Exception as exc:
                logger.error("Failed to load encoding for %s: %s", sid, exc)
    logger.info("Loaded %d face encodings from database.", len(encodings))
    return encodings


def save_encoding(student_id: str, encoding: np.ndarray, confidence: float = 1.0) -> bool:
    """Persist a face encoding to the database.

    Args:
        student_id: Student ID this encoding belongs to.
        encoding: 128-dim numpy array.
        confidence: Optional quality metric.

    Returns:
        True on success.
    """
    blob = save_encoding_to_blob(encoding)
    db.execute_insert(
        "INSERT INTO face_encodings (student_id, encoding, confidence) VALUES (?, ?, ?)",
        (student_id, blob, confidence),
    )
    logger.info("Saved encoding for student: %s", student_id)
    return True


def update_encoding(student_id: str, new_encoding: np.ndarray) -> bool:
    """Append a new encoding for an existing student.

    Args:
        student_id: Target student.
        new_encoding: New 128-dim numpy array.

    Returns:
        True on success.
    """
    return save_encoding(student_id, new_encoding)


def delete_encodings(student_id: str) -> int:
    """Remove all encodings for a student.

    Args:
        student_id: Student ID.

    Returns:
        Number of rows deleted.
    """
    return db.execute_update(
        "DELETE FROM face_encodings WHERE student_id = ?", (student_id,)
    )


def load_encodings_from_images(dataset_dir: str = DATASET_DIR) -> bool:
    """Placeholder: generate and store encodings from dataset images.

    This function requires face_recognition to be installed. It scans:
        dataset_dir/{student_name}/*.jpg

    When face_recognition is available, replace the body with actual encoding logic.

    Args:
        dataset_dir: Root directory containing per-student image subfolders.

    Returns:
        True if face_recognition is available and encodings were processed, False otherwise.
    """
    try:
        import face_recognition  # noqa: F401
    except ImportError:
        logger.warning(
            "face_recognition not installed. Skipping image-based encoding generation. "
            "Install face_recognition to enable face recognition."
        )
        return False

    # --- face_recognition encoding logic goes here when available ---
    logger.info("face_recognition detected — encoding generation from %s would proceed here.", dataset_dir)
    return True

"""
test_face_recognition.py — Tests for face recognition engine and encoding manager.
Actual dlib tests only run when dlib is installed.
"""

import io
import os
import sys
import pytest
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.encoding_manager import save_encoding_to_blob, load_encoding_from_blob
from backend.face_recognition_engine import FaceRecognitionEngine

try:
    import dlib
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False


def test_encoding_blob_roundtrip():
    """Verify numpy array serializes and deserializes correctly."""
    original = np.random.rand(128).astype(np.float64)
    blob = save_encoding_to_blob(original)
    restored = load_encoding_from_blob(blob)
    np.testing.assert_array_almost_equal(original, restored)


def test_face_engine_no_encodings():
    """FaceRecognitionEngine returns empty results with no encodings."""
    engine = FaceRecognitionEngine({})
    assert engine.known_encodings == {}

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    results = engine.recognize_frame(dummy_frame)
    assert isinstance(results, list)


def test_face_engine_match_face():
    """Verify match_face returns correct student for identical encoding."""
    known_enc = np.random.rand(128).astype(np.float64)
    engine = FaceRecognitionEngine({"STU-001": known_enc})

    # Exact same encoding → should match
    sid, conf = engine.match_face(known_enc, threshold=0.45)
    assert sid == "STU-001"
    assert conf > 0.0


def test_face_engine_no_match():
    """Verify random encoding does not match stored one beyond threshold."""
    known_enc = np.zeros(128, dtype=np.float64)
    engine = FaceRecognitionEngine({"STU-001": known_enc})

    # Very different encoding
    far_enc = np.ones(128, dtype=np.float64) * 10.0
    sid, conf = engine.match_face(far_enc, threshold=0.45)
    assert sid is None
    assert conf == 0.0


def test_face_engine_reload_encodings():
    """Verify reload updates in-memory encodings."""
    engine = FaceRecognitionEngine({})
    assert len(engine.known_encodings) == 0

    new_enc = {"STU-NEW": np.random.rand(128)}
    engine.reload_encodings(new_enc)
    assert "STU-NEW" in engine.known_encodings


@pytest.mark.skipif(not DLIB_AVAILABLE, reason="dlib not installed")
def test_detect_faces_dlib():
    """Test face detection on a blank frame (no faces → empty list)."""
    import cv2
    engine = FaceRecognitionEngine({})
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    faces = engine.detect_faces(blank)
    assert isinstance(faces, list)
    assert len(faces) == 0  # No faces in blank frame

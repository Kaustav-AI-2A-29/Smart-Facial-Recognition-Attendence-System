"""
face_recognition_engine.py — Multi-face detection, encoding, and matching.
Note: Requires face_recognition to be installed.
Gracefully stubs when face_recognition is unavailable.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.48"))
PROCESS_EVERY_N = int(os.getenv("PROCESS_EVERY_N", "2"))

try:
    import face_recognition
    _FR_AVAILABLE = True
except ImportError:
    _FR_AVAILABLE = False
    logger.warning("face_recognition not installed. FaceRecognitionEngine will return empty results.")


class FaceRecognitionEngine:
    """Multi-face detection, encoding, and matching using face_recognition.

    When face_recognition is unavailable, all methods return safe empty defaults.
    """

    def __init__(self, face_encodings_dict: Dict[str, np.ndarray] = None):
        """Initialize with pre-loaded face encodings.

        Args:
            face_encodings_dict: Mapping of student_id → 128-dim numpy array.
        """
        self.known_encodings: Dict[str, np.ndarray] = face_encodings_dict or {}
        self._frame_count = 0

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect all faces in a BGR frame.

        Args:
            frame: OpenCV BGR numpy array.

        Returns:
            List of (x, y, w, h) bounding boxes.
        """
        if not _FR_AVAILABLE:
            return []
        import cv2
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Returns (top, right, bottom, left)
        css_boxes = face_recognition.face_locations(rgb)
        
        boxes = []
        for top, right, bottom, left in css_boxes:
            x, y = max(0, left), max(0, top)
            w = right - left
            h = bottom - top
            boxes.append((x, y, w, h))
        return boxes

    def get_face_encoding(
        self, frame: np.ndarray, face_location: Tuple[int, int, int, int]
    ) -> Optional[np.ndarray]:
        """Generate a 128-dim face encoding for a detected face.

        Args:
            frame: OpenCV BGR frame.
            face_location: (x, y, w, h) bounding box.

        Returns:
            128-dimensional numpy array, or None if unavailable.
        """
        if not _FR_AVAILABLE:
            return None
        import cv2
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        x, y, w, h = face_location
        # Convert back to css format (top, right, bottom, left)
        css_box = (y, x + w, y + h, x)
        
        encodings = face_recognition.face_encodings(rgb, known_face_locations=[css_box])
        if encodings:
            return encodings[0]
        return None

    def match_face(
        self, encoding: np.ndarray, threshold: float = MATCH_THRESHOLD
    ) -> Tuple[Optional[str], float]:
        """Match an encoding against stored known encodings.

        Args:
            encoding: 128-dim numpy array.
            threshold: Euclidean distance threshold for a match.

        Returns:
            (student_id, confidence) if matched, (None, 0.0) otherwise.
            confidence = 1.0 - euclidean_distance
        """
        if not self.known_encodings:
            return None, 0.0

        best_id = None
        best_dist = float("inf")
        for sid, known_enc in self.known_encodings.items():
            dist = float(np.linalg.norm(encoding - known_enc))
            if dist < best_dist:
                best_dist = dist
                best_id = sid

        if best_dist <= threshold:
            confidence = round(1.0 - best_dist, 4)
            return best_id, confidence
        return None, 0.0

    def recognize_frame(self, frame: np.ndarray) -> List[Dict]:
        """Full pipeline: detect → encode → match for one frame.

        Args:
            frame: OpenCV BGR frame.

        Returns:
            List of result dicts with keys:
            face_location, encoding, student_id, confidence, status.
        """
        self._frame_count += 1
        if self._frame_count % PROCESS_EVERY_N != 0:
            return []

        results = []
        face_locations = self.detect_faces(frame)
        for loc in face_locations:
            encoding = self.get_face_encoding(frame, loc)
            if encoding is None:
                results.append({
                    "face_location": loc,
                    "encoding": None,
                    "student_id": None,
                    "confidence": 0.0,
                    "status": "unknown",
                })
                continue

            student_id, confidence = self.match_face(encoding)
            results.append({
                "face_location": loc,
                "encoding": encoding,
                "student_id": student_id,
                "confidence": confidence,
                "status": "matched" if student_id else "unknown",
            })
        return results

    def reload_encodings(self, new_encodings: Dict[str, np.ndarray]) -> None:
        """Replace in-memory encodings (e.g., after adding a new student).

        Args:
            new_encodings: Updated {student_id: encoding} dict.
        """
        self.known_encodings = new_encodings
        logger.info("Reloaded %d face encodings.", len(new_encodings))

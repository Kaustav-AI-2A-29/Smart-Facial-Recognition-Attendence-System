"""
face_recognition_engine.py — Multi-face detection, encoding, and matching.
Note: Requires dlib + shape_predictor_68_face_landmarks.dat to be installed.
Gracefully stubs when dlib is unavailable.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.45"))
PROCESS_EVERY_N = int(os.getenv("PROCESS_EVERY_N", "2"))

try:
    import dlib
    _DLIB_AVAILABLE = True
except ImportError:
    _DLIB_AVAILABLE = False
    logger.warning("dlib not installed. FaceRecognitionEngine will return empty results.")


class FaceRecognitionEngine:
    """Multi-face detection, encoding, and matching using dlib.

    When dlib is unavailable (e.g., during initial setup), all methods
    return safe empty defaults so the rest of the app can still run.
    """

    def __init__(self, face_encodings_dict: Dict[str, np.ndarray] = None):
        """Initialize with pre-loaded face encodings.

        Args:
            face_encodings_dict: Mapping of student_id → 128-dim numpy array.
        """
        self.known_encodings: Dict[str, np.ndarray] = face_encodings_dict or {}
        self._detector = None
        self._shape_predictor = None
        self._face_rec_model = None
        self._frame_count = 0

        if _DLIB_AVAILABLE:
            self._init_dlib()

    def _init_dlib(self) -> None:
        """Load dlib models."""
        try:
            self._detector = dlib.get_frontal_face_detector()
            landmarks_path = os.getenv(
                "LANDMARKS_DAT", "shape_predictor_68_face_landmarks.dat"
            )
            rec_model_path = os.getenv(
                "FACE_REC_DAT", "dlib_face_recognition_resnet_model_v1.dat"
            )
            if os.path.exists(landmarks_path):
                self._shape_predictor = dlib.shape_predictor(landmarks_path)
            else:
                logger.warning("Landmarks model not found: %s", landmarks_path)

            if os.path.exists(rec_model_path):
                self._face_rec_model = dlib.face_recognition_model_v1(rec_model_path)
            else:
                logger.warning("Face rec model not found: %s", rec_model_path)
        except Exception as exc:
            logger.error("Failed to initialize dlib models: %s", exc)

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect all faces in a BGR frame.

        Args:
            frame: OpenCV BGR numpy array.

        Returns:
            List of (x, y, w, h) bounding boxes.
        """
        if not _DLIB_AVAILABLE or self._detector is None:
            return []
        import cv2
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detections = self._detector(rgb, 1)
        boxes = []
        for d in detections:
            x, y = max(0, d.left()), max(0, d.top())
            w = d.right() - d.left()
            h = d.bottom() - d.top()
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
        if not _DLIB_AVAILABLE or self._shape_predictor is None or self._face_rec_model is None:
            return None
        import cv2
        import dlib
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        x, y, w, h = face_location
        rect = dlib.rectangle(x, y, x + w, y + h)
        shape = self._shape_predictor(rgb, rect)
        encoding = np.array(self._face_rec_model.compute_face_descriptor(rgb, shape))
        return encoding

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

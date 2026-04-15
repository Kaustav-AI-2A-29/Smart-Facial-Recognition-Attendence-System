"""
liveness_detector.py — Eye Aspect Ratio and head yaw based anti-spoofing.
Requires face_recognition landmarks. Gracefully stubs when unavailable.
"""

import logging
import math
import os
import time
from typing import Any, Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)

LIVENESS_BLINK_FRAMES = int(os.getenv("LIVENESS_BLINK_FRAMES", "5"))
LIVENESS_YAW_THRESHOLD = float(os.getenv("LIVENESS_YAW_THRESHOLD", "15"))
LIVENESS_WINDOW_SECONDS = int(os.getenv("LIVENESS_WINDOW_SECONDS", "3"))
EAR_BLINK_THRESHOLD = 0.20


def _point_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    """Euclidean distance between two (x, y) points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


class LivenessDetector:
    """Detects liveness via blink detection (EAR) and head yaw estimation.

    When face_recognition is unavailable, is_live() returns True to avoid blocking the UI.
    """

    def __init__(
        self,
        time_window_seconds: int = LIVENESS_WINDOW_SECONDS,
        blink_threshold: float = EAR_BLINK_THRESHOLD,
        yaw_threshold: float = LIVENESS_YAW_THRESHOLD,
        blink_frames: int = LIVENESS_BLINK_FRAMES,
    ):
        self.time_window = time_window_seconds
        self.blink_threshold = blink_threshold
        self.yaw_threshold = yaw_threshold
        self.blink_frames = blink_frames

        self._blink_count = 0
        self._consecutive_low_ear = 0
        self._start_time = time.time()
        self._yaw_detected = False

    def calculate_eye_aspect_ratio(self, landmarks: Dict[str, List[Tuple[int, int]]]) -> float:
        """Compute EAR from face_recognition landmarks.

        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

        Args:
            landmarks: Dictionary of facial features.

        Returns:
            Average EAR for both eyes.
        """
        def eye_ear(pts) -> float:
            if len(pts) != 6:
                return 0.0
            a = _point_distance(pts[1], pts[5])
            b = _point_distance(pts[2], pts[4])
            c = _point_distance(pts[0], pts[3])
            return (a + b) / (2.0 * c) if c > 0 else 0.0

        if 'left_eye' not in landmarks or 'right_eye' not in landmarks:
            return 0.0

        left_pts = landmarks['left_eye']
        right_pts = landmarks['right_eye']
        return (eye_ear(left_pts) + eye_ear(right_pts)) / 2.0

    def calculate_head_yaw(self, landmarks: Dict[str, List[Tuple[int, int]]]) -> float:
        """Estimate horizontal head yaw angle from nose bridge and tip.

        Uses bridge and nose tip relative to face width via the chin landmarks.

        Args:
            landmarks: Dictionary of facial features.

        Returns:
            Approximate yaw angle in degrees.
        """
        if 'nose_bridge' not in landmarks or 'chin' not in landmarks:
            return 0.0

        nose_bridge = landmarks['nose_bridge'][0]
        nose_tip = landmarks['nose_bridge'][-1]
        
        chin = landmarks['chin']
        left_ear = chin[0]
        right_ear = chin[-1]

        face_width = _point_distance(left_ear, right_ear)
        if face_width == 0:
            return 0.0

        midpoint_x = (left_ear[0] + right_ear[0]) / 2.0
        offset = nose_tip[0] - midpoint_x
        yaw_degrees = (offset / face_width) * 90
        return yaw_degrees

    def update(self, landmarks: Dict[str, List[Tuple[int, int]]]) -> None:
        """Update detector state with new frame landmarks.

        Args:
            landmarks: face_recognition facial features dictionary for a face.
        """
        now = time.time()
        if now - self._start_time > self.time_window:
            self._reset_window()

        ear = self.calculate_eye_aspect_ratio(landmarks)
        if ear < self.blink_threshold:
            self._consecutive_low_ear += 1
        else:
            if self._consecutive_low_ear >= self.blink_frames:
                self._blink_count += 1
                logger.debug("Blink detected (EAR=%.3f)", ear)
            self._consecutive_low_ear = 0

        yaw = self.calculate_head_yaw(landmarks)
        if abs(yaw) > self.yaw_threshold:
            self._yaw_detected = True
            logger.debug("Head yaw detected: %.1f°", yaw)

    def is_live(self, landmarks: Optional[Dict[str, List[Tuple[int, int]]]] = None) -> bool:
        """Check if the face passes the liveness test.

        Args:
            landmarks: Optional face_recognition landmarks to update before checking.

        Returns:
            True if blink OR head movement detected within the time window.
            True unconditionally if face_recognition is unavailable.
        """
        try:
            import face_recognition  # noqa: F401
        except ImportError:
            return True  # Fail-open: liveness check skipped when face_recognition missing

        if landmarks is not None:
            self.update(landmarks)

        return self._blink_count > 0 or self._yaw_detected

    def reset(self) -> None:
        """Fully reset the detector state (call between students)."""
        self._blink_count = 0
        self._consecutive_low_ear = 0
        self._start_time = time.time()
        self._yaw_detected = False

    def _reset_window(self) -> None:
        """Reset only the time window counters (not full reset)."""
        self._blink_count = 0
        self._yaw_detected = False
        self._start_time = time.time()

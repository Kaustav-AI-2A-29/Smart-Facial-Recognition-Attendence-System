"""
liveness_detector.py — Eye Aspect Ratio and head yaw based anti-spoofing.
Requires dlib landmarks. Gracefully stubs when dlib is unavailable.
"""

import logging
import math
import os
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

LIVENESS_BLINK_FRAMES = int(os.getenv("LIVENESS_BLINK_FRAMES", "5"))
LIVENESS_YAW_THRESHOLD = float(os.getenv("LIVENESS_YAW_THRESHOLD", "15"))
LIVENESS_WINDOW_SECONDS = int(os.getenv("LIVENESS_WINDOW_SECONDS", "3"))
EAR_BLINK_THRESHOLD = 0.20


def _point_distance(p1: Any, p2: Any) -> float:
    """Euclidean distance between two dlib points."""
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


class LivenessDetector:
    """Detects liveness via blink detection (EAR) and head yaw estimation.

    When dlib is unavailable, is_live() returns True to avoid blocking the UI.
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

    def calculate_eye_aspect_ratio(self, landmarks: Any) -> float:
        """Compute EAR from dlib 68-point landmarks.

        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        Left eye: landmarks 36-41, Right eye: landmarks 42-47.

        Args:
            landmarks: dlib full_object_detection (68 points).

        Returns:
            Average EAR for both eyes.
        """
        def eye_ear(pts) -> float:
            a = _point_distance(pts[1], pts[5])
            b = _point_distance(pts[2], pts[4])
            c = _point_distance(pts[0], pts[3])
            return (a + b) / (2.0 * c) if c > 0 else 0.0

        left_pts = [landmarks.part(i) for i in range(36, 42)]
        right_pts = [landmarks.part(i) for i in range(42, 48)]
        return (eye_ear(left_pts) + eye_ear(right_pts)) / 2.0

    def calculate_head_yaw(self, landmarks: Any) -> float:
        """Estimate horizontal head yaw angle from nose bridge and tip.

        Uses bridge (point 27) and nose tip (point 30) relative to face width.

        Args:
            landmarks: dlib full_object_detection.

        Returns:
            Approximate yaw angle in degrees.
        """
        nose_bridge = landmarks.part(27)
        nose_tip = landmarks.part(30)
        left_ear = landmarks.part(0)
        right_ear = landmarks.part(16)

        face_width = _point_distance(left_ear, right_ear)
        if face_width == 0:
            return 0.0

        midpoint_x = (left_ear.x + right_ear.x) / 2
        offset = nose_tip.x - midpoint_x
        yaw_degrees = (offset / face_width) * 90
        return yaw_degrees

    def update(self, landmarks: Any) -> None:
        """Update detector state with new frame landmarks.

        Args:
            landmarks: dlib full_object_detection for a face.
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

    def is_live(self, landmarks: Optional[Any] = None) -> bool:
        """Check if the face passes the liveness test.

        Args:
            landmarks: Optional dlib landmarks to update before checking.

        Returns:
            True if blink OR head movement detected within the time window.
            True unconditionally if dlib is unavailable (fail-open for dev).
        """
        try:
            import dlib  # noqa: F401
        except ImportError:
            return True  # Fail-open: liveness check skipped when dlib missing

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

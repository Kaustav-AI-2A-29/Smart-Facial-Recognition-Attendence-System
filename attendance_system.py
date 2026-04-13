"""
Face Recognition Attendance System
====================================
Requirements:
    pip install face_recognition opencv-python numpy

Dataset Structure:
    dataset/
        person_name/
            image1.jpg
            image2.jpg
"""

import face_recognition
import cv2
import numpy as np
import csv
import os
from datetime import datetime
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
DATASET_DIR       = "dataset"       # folder containing sub-folders per person
ATTENDANCE_FILE   = "attendance.csv"
MATCH_THRESHOLD   = 0.48            # lower = stricter match (tightened for accuracy)
CONFIRM_FRAMES    = 10              # consecutive frames needed to confirm identity
PROCESS_EVERY_N   = 2               # process every Nth frame (performance)


# ─────────────────────────────────────────────
#  STEP 1 – LOAD DATASET & BUILD ENCODINGS
# ─────────────────────────────────────────────
def load_dataset(dataset_dir: str):
    """
    Walk dataset/ directory.
    Each sub-folder name  →  person name.
    Each image inside     →  face encoding.
    Returns (known_encodings, known_names).
    """
    known_encodings = []
    known_names     = []

    if not os.path.isdir(dataset_dir):
        print(f"[ERROR] Dataset folder '{dataset_dir}' not found.")
        return known_encodings, known_names

    for person_name in os.listdir(dataset_dir):
        person_dir = os.path.join(dataset_dir, person_name)
        if not os.path.isdir(person_dir):
            continue

        image_count = 0
        for filename in os.listdir(person_dir):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            image_path = os.path.join(person_dir, filename)

            # Use cv2 to load — handles JPEG, PNG, RGBA, grayscale, etc.
            bgr_image = cv2.imread(image_path)
            if bgr_image is None:
                print(f"  [WARN] Could not read image: {image_path}")
                continue

            # face_recognition expects RGB, not BGR
            rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

            encodings = face_recognition.face_encodings(rgb_image)

            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(person_name)
                image_count += 1
            else:
                print(f"  [WARN] No face found in: {image_path}")

        print(f"  Loaded {image_count} encoding(s) for: {person_name}")

    print(f"\n[INFO] Dataset ready – {len(known_encodings)} total encoding(s) "
          f"for {len(set(known_names))} person(s).\n")
    return known_encodings, known_names


# ─────────────────────────────────────────────
#  STEP 2 – ATTENDANCE FILE HELPERS
# ─────────────────────────────────────────────
def load_todays_attendance(filepath: str) -> set:
    """Return a set of names already marked today."""
    marked = set()
    today  = datetime.now().strftime("%Y-%m-%d")

    if not os.path.isfile(filepath):
        return marked

    with open(filepath, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3 and row[2] == today:
                marked.add(row[0])
    return marked


def mark_attendance(name: str, filepath: str, marked_today: set):
    """Append a new attendance record if not already marked today."""
    if name in marked_today:
        return  # already recorded

    now   = datetime.now()
    today = now.strftime("%Y-%m-%d")
    time  = now.strftime("%H:%M:%S")

    with open(filepath, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([name, time, today])

    marked_today.add(name)
    print(f"[ATTENDANCE] v {name} marked at {time} on {today}")


# ─────────────────────────────────────────────
#  STEP 3 – FACE MATCHING
# ─────────────────────────────────────────────
def identify_face(face_encoding, known_encodings, known_names, threshold):
    """
    Compare face_encoding against all known encodings.
    Returns the best-matching name or 'Unknown'.
    """
    if not known_encodings:
        return "Unknown"

    distances = face_recognition.face_distance(known_encodings, face_encoding)
    best_idx  = int(np.argmin(distances))
    best_dist = distances[best_idx]

    # Debug: show best candidate and its distance on every processed frame
    print(f"[DEBUG] Best match: {known_names[best_idx]} | Distance: {best_dist:.3f}")

    # Strict matching – must beat threshold, otherwise treat as Unknown
    if best_dist < threshold:
        return known_names[best_idx]
    else:
        return "Unknown"


# ─────────────────────────────────────────────
#  STEP 4 – STABILITY TRACKER
# ─────────────────────────────────────────────
class StabilityTracker:
    """
    Tracks a detected name across frames.
    Identity is confirmed only when the same name appears
    for CONFIRM_FRAMES consecutive frames.
    """

    def __init__(self, required_frames: int):
        self.required_frames  = required_frames
        self.candidate        = None   # current candidate name
        self.streak           = 0      # consecutive frames for candidate
        self.confirmed        = None   # locked confirmed name
        self.confirmed_locked = False  # True once identity is confirmed

    def update(self, detected_name: str):
        """
        Feed the latest detected name.
        Returns (confirmed_name_or_None, display_name).
        confirmed_name_or_None  →  non-None only on the frame of confirmation
        display_name            →  what to show in the UI right now
        """
        if self.confirmed_locked:
            # Already confirmed; keep showing the locked name
            return None, self.confirmed

        if detected_name == self.candidate:
            self.streak += 1
        else:
            self.candidate = detected_name
            self.streak    = 1

        # Check confirmation threshold
        if self.streak >= self.required_frames and self.candidate != "Unknown":
            self.confirmed        = self.candidate
            self.confirmed_locked = True
            return self.confirmed, self.confirmed  # newly confirmed

        return None, self.candidate  # still building streak

    def reset(self):
        """Call this after attendance is marked to allow next detection."""
        self.candidate        = None
        self.streak           = 0
        self.confirmed        = None
        self.confirmed_locked = False


# ─────────────────────────────────────────────
#  STEP 5 – DRAW OVERLAY ON FRAME
# ─────────────────────────────────────────────
def draw_face_box(frame, top, right, bottom, left, name, confirmed: bool):
    """
    Green box  + name  →  confirmed identity
    Orange box + label →  unknown / still detecting
    """
    color = (0, 200, 0) if confirmed else (0, 140, 255)

    # Bounding box
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

    # Label background
    label = name
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    cv2.rectangle(frame, (left, bottom), (left + tw + 10, bottom + th + 12), color, -1)

    # Label text
    cv2.putText(frame, label, (left + 5, bottom + th + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)


def draw_status_bar(frame, tracker: StabilityTracker, marked_today: set):
    """Draw a small status overlay at the top of the frame."""
    status_lines = [
        f"Marked today: {', '.join(sorted(marked_today)) if marked_today else 'None'}",
        "Press 'Q' to quit  |  Press 'R' to reset attendance",
    ]
    for i, line in enumerate(status_lines):
        cv2.putText(frame, line, (10, 25 + i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)


# ─────────────────────────────────────────────
#  EXCEL EXPORT
# ─────────────────────────────────────────────
def export_to_excel(csv_filepath: str, excel_filepath: str = "attendance.xlsx"):
    """
    Convert attendance CSV to a formatted Excel file.
    """
    if not OPENPYXL_AVAILABLE:
        print("[ERROR] openpyxl not installed. Install with: pip install openpyxl")
        return False

    if not os.path.isfile(csv_filepath):
        print(f"[ERROR] Attendance file '{csv_filepath}' not found.")
        return False

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    # Define styles
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    center_align = Alignment(horizontal="center", vertical="center")
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    # Add headers
    headers = ["Name", "Time (HH:MM:SS)", "Date (YYYY-MM-DD)"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border

    # Read CSV and add data
    row_num = 2
    with open(csv_filepath, "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            for col_num, value in enumerate(row, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = value
                cell.alignment = center_align
                cell.border = border
            row_num += 1

    # Auto-adjust column widths
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 20

    # Save
    wb.save(excel_filepath)
    print(f"[SUCCESS] Attendance exported to: {excel_filepath}")
    return True


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  Face Recognition Attendance System")
    print("=" * 50)

    # 1. Load dataset
    known_encodings, known_names = load_dataset(DATASET_DIR)
    if not known_encodings:
        print("[ERROR] No encodings loaded. Check your dataset folder.")
        return

    # 2. Fresh start – wipe CSV and begin with empty attendance set
    marked_today = set()
    open(ATTENDANCE_FILE, 'w').close()
    print("[INFO] Fresh session started. attendance.csv cleared.")

    # 3. Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open webcam. Check camera connection.")
        return

    print("[INFO] Webcam started. Press 'Q' to quit.\n")

    tracker   = StabilityTracker(required_frames=CONFIRM_FRAMES)
    frame_num = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Failed to grab frame. Retrying...")
            continue

        frame_num += 1

        # ── Process every Nth frame for performance ──
        if frame_num % PROCESS_EVERY_N == 0:

            # Resize to speed up recognition
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small   = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Detect faces
            face_locations = face_recognition.face_locations(rgb_small, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

            if face_encodings:
                # Use first detected face (single-person scenario)
                face_enc = face_encodings[0]
                loc      = face_locations[0]  # top, right, bottom, left (at 50% scale)

                # Scale coordinates back to original frame size
                top, right, bottom, left = [v * 2 for v in loc]

                # Identify
                raw_name = identify_face(face_enc, known_encodings, known_names, MATCH_THRESHOLD)

                # Prevent unknown faces from polluting the streak tracker
                if raw_name == "Unknown":
                    tracker.update("Unknown")
                    draw_face_box(frame, top, right, bottom, left, "Unknown", False)
                    # Fall through to the single waitKey handler below

                else:
                    # Stability check
                    newly_confirmed, display_name = tracker.update(raw_name)

                    # Mark attendance on confirmation
                    if newly_confirmed and newly_confirmed not in marked_today:
                        mark_attendance(newly_confirmed, ATTENDANCE_FILE, marked_today)
                        # Show confirmation banner for 2 seconds then reset tracker
                        cv2.putText(frame, f"ATTENDANCE MARKED: {newly_confirmed}",
                                    (10, frame.shape[0] - 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        draw_status_bar(frame, tracker, marked_today)
                        cv2.imshow("Attendance System", frame)
                        cv2.waitKey(2000)
                        tracker.reset()
                        continue

                    # Draw box
                    confirmed_disp = tracker.confirmed_locked
                    draw_face_box(frame, top, right, bottom, left, display_name, confirmed_disp)

            else:
                # No face detected – slowly decay streak but don't hard-reset
                if not tracker.confirmed_locked:
                    tracker.streak = max(0, tracker.streak - 1)

        # ── Always draw status bar ──
        draw_status_bar(frame, tracker, marked_today)

        cv2.imshow("Attendance System", frame)

        # ── Single, centralised key handler ──
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("\n[INFO] Quit requested by user.")
            break

        if key == ord('r'):
            # Reset: clear memory, wipe CSV, reset tracker
            print("[INFO] Resetting attendance...")
            marked_today.clear()
            open(ATTENDANCE_FILE, 'w').close()
            tracker.reset()
            print("[INFO] Attendance cleared. CSV wiped. Tracker reset.")
            # Brief on-screen confirmation
            cv2.putText(frame, "RESET DONE", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.imshow("Attendance System", frame)
            cv2.waitKey(1000)

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Session ended.")
    if marked_today:
        print(f"[INFO] Attendance marked for: {', '.join(sorted(marked_today))}")


if __name__ == "__main__":
    import sys

    print("\n" + "=" * 50)
    print("  Attendance System Menu")
    print("=" * 50)
    print("1. Run face recognition (default)")
    print("2. Export attendance to Excel")
    print("="*50)

    choice = input("\nSelect option (1/2) [default=1]: ").strip()

    if choice == "2":
        export_to_excel(ATTENDANCE_FILE)
    else:
        main()

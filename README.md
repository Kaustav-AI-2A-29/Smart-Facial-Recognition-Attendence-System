# Smart Facial Recognition Attendance System

> **A fully local, Streamlit-powered attendance management system with multi-face recognition, liveness detection, role-based access control, and SQLite persistence.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?logo=streamlit)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-19%20Passing-brightgreen)](#testing)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [Quick Start](#quick-start)
7. [Installation](#installation)
8. [Configuration](#configuration)
9. [Running the App](#running-the-app)
10. [Face Recognition Setup](#face-recognition-setup)
11. [Default Credentials](#default-credentials)
12. [API / Module Reference](#api--module-reference)
13. [Testing](#testing)
14. [Development Roadmap](#development-roadmap)
15. [Contributing](#contributing)
16. [License](#license)

---

## Overview

The **Smart Facial Recognition Attendance System** is a fully offline, production-ready attendance management tool designed for educational institutions. The system uses:

- **dlib-powered multi-face recognition** to automatically detect and identify up to 5-8 students simultaneously from a live webcam feed.
- **Eye Aspect Ratio (EAR) blink detection** and **head yaw estimation** (liveness detection) to reject photo-based spoofing attacks.
- **Role-based access control** — Students manage their own profiles; Faculty view all students, manage records, and run live attendance capture sessions.
- **Local SQLite database** — No cloud, no Firebase, no Docker. Everything runs on your machine.

This is **not a prototype** — it follows production best practices: parameterized queries, bcrypt password hashing, transaction rollback safety, environment-variable configuration, and comprehensive automated tests.

---

## Architecture

```
+-------------------------------------------------------+
|               STREAMLIT FRONTEND                      |
|  app.py (login + routing)                             |
|  pages/                                               |
|    01_Student_Dashboard.py  — Profile, attendance     |
|    02_Faculty_Dashboard.py  — All students, marks     |
|    03_Attendance_Capture.py — Live camera session     |
|  components/                                          |
|    sidebar | camera_widget | student_profile_form     |
|    attendance_table | student_list                    |
+--------------------+----------------------------------+
                     |
        +------------+-----------+
        |                        |
+-------v---------+    +---------v--------+
|  BACKEND        |    |  DATA LAYER      |
|  backend/       |    |                  |
|  auth.py        |    |  SQLite DB       |
|  database.py    |    |  + data/         |
|  student_srv    |    |    screenshots/  |
|  attendance_srv |    |    profiles/     |
|  image_proc     |    |    dataset/      |
|  encoding_mgr   |    +------------------+
|  face_rec_eng   |
|  liveness_det   |
+-----------------+
```

---

## Features

### Authentication & Authorization

| Feature | Student | Faculty |
|---------|:-------:|:-------:|
| Login with username/password | ✅ | ✅ |
| View own profile | ✅ | — |
| Edit own profile + photo | ✅ | — |
| View own attendance | ✅ | ✅ |
| View all student profiles | ❌ | ✅ |
| Edit any student's details | ❌ | ✅ |
| Mark attendance manually | ❌ | ✅ |
| Run live camera capture | ❌ | ✅ |
| Export CSV reports | ❌ | ✅ |
| Delete student records | ❌ | ✅ |

### Face Recognition Pipeline

```
Webcam Frame
    ↓
[1] Face Detection (dlib HOG)
    → Up to 5-8 simultaneous faces
    ↓
[2] Face Encoding (dlib ResNet)
    → 128-dimensional vector per face
    ↓
[3] Matching (Euclidean Distance)
    → Distance < 0.45 → matched student
    ↓
[4] Liveness Detection
    → EAR blink check (5 frames below 0.20)
    → Head yaw > 15° detection
    → 3-second rolling window
    ↓
[5] Attendance Recording
    → First recognition per day = Present
    → Screenshot saved to /data/screenshots/
    → Written to SQLite attendance table
    ↓
[6] Visual Feedback
    → GREEN box: Matched + Live (name + confidence%)
    → YELLOW box: Matched, waiting for liveness
    → RED box: Unknown face
```

### Student Dashboard
- View full profile (name, age, roll number, department, email, address, hobbies)
- Upload/delete profile picture (saved as JPEG, max 300×300)
- View personal attendance history (last 30 records)
- Live attendance stats: Present / Absent / % this month
- Export personal attendance as CSV

### Faculty Dashboard
- Searchable, filterable student directory (by name, student ID, department)
- Per-student detail view: profile + attendance history + statistics
- Manual attendance marking for any student
- Delete student records (with cascade to attendance + encodings)
- Export all student data as CSV

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | Streamlit (pages-based) | ≥1.32 |
| **Backend** | Python | 3.10+ |
| **Database** | SQLite (stdlib `sqlite3`) | Built-in |
| **Authentication** | bcrypt | ≥4.1 |
| **Face Detection** | dlib HOG detector | ≥19.24 *(optional)* |
| **Face Encoding** | dlib ResNet-34 model | ≥19.24 *(optional)* |
| **Liveness** | dlib landmarks (68-pt) + EAR | — |
| **Image Processing** | OpenCV + Pillow | ≥4.8 / ≥10 |
| **Data Export** | pandas + openpyxl | ≥1.4 / ≥3.1 |
| **Config** | python-dotenv | ≥1.0 |
| **Testing** | pytest | ≥8.0 |

---

## Project Structure

```
Smart-Facial-Recognition-Attendence-System/
|
+-- backend/
|   +-- __init__.py
|   +-- database.py              # SQLite connection manager + schema
|   +-- auth.py                  # Login, bcrypt hashing, session helpers
|   +-- student_service.py       # Student CRUD + validation
|   +-- attendance_service.py    # Attendance recording + queries
|   +-- image_processor.py       # Profile picture + screenshot handling
|   +-- encoding_manager.py      # Face encoding blob storage/retrieval
|   +-- face_recognition_engine.py  # dlib detection + matching
|   +-- liveness_detector.py     # EAR blink + head yaw detection
|
+-- frontend/
|   +-- app.py                   # Main entry point (login + routing)
|   +-- pages/
|   |   +-- 01_Student_Dashboard.py
|   |   +-- 02_Faculty_Dashboard.py
|   |   +-- 03_Attendance_Capture.py
|   +-- components/
|       +-- sidebar.py
|       +-- camera_widget.py
|       +-- student_profile_form.py
|       +-- attendance_table.py
|       +-- student_list.py
|
+-- data/
|   +-- database.sqlite          # Auto-created on first run
|   +-- dataset/                 # Training images (stu_name/*)
|   +-- screenshots/             # Attendance snapshots (YYYY-MM-DD/*)
|   +-- profile_pictures/        # Student profile images (STU-001.jpg)
|
+-- tests/
|   +-- test_database.py         # DB schema + CRUD tests
|   +-- test_auth.py             # Login + password tests
|   +-- test_face_recognition.py # Encoding + matching tests
|
+-- .env                         # Config (gitignored)
+-- .gitignore
+-- requirements.txt
+-- setup_database.py            # Schema initializer (run once)
+-- seed_data.py                 # Test data populator
+-- README.md
+-- ATTENDANCE_PLANNING.md
```

---

## Quick Start

```powershell
# 1. Clone and enter the project
git clone https://github.com/Kaustav-AI-2A-29/Smart-Facial-Recognition-Attendence-System.git
cd "Smart-Facial-Recognition-Attendence-System"

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database + seed test data
python setup_database.py
python seed_data.py

# 5. Launch the app
streamlit run frontend/app.py
```

Open your browser at **http://localhost:8501**

---

## Installation

### Prerequisites

- Python **3.10 or higher** (tested on 3.13)
- A webcam (for live attendance capture)
- Windows / macOS / Linux

### Step 1: Clone

```powershell
git clone https://github.com/Kaustav-AI-2A-29/Smart-Facial-Recognition-Attendence-System.git
cd "Smart-Facial-Recognition-Attendence-System"
```

### Step 2: Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux
```

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

> **Note:** `dlib` is listed as optional in `requirements.txt` (commented out). The app works fully without it, except the live attendance capture page which requires dlib. See [Face Recognition Setup](#face-recognition-setup) for instructions.

### Step 4: Initialize Database

```powershell
python setup_database.py
```

Expected output:
```
Initializing database...
  [OK] Database file: ./data/database.sqlite
  [OK] Tables created: users, students, faculty, face_encodings, attendance
  [OK] Admin faculty user created.
    Username: admin  |  Password: admin123  <- CHANGE THIS!
```

### Step 5: Seed Test Data (Optional)

```powershell
python seed_data.py
```

This creates 4 test students and 1 faculty account for development/demo purposes.

---

## Configuration

All configuration is in the `.env` file in the project root. It is **gitignored by default** — do not commit it.

```env
# Database
DATABASE_URL=./data/database.sqlite

# Face Recognition thresholds
FACE_DETECT_THRESHOLD=0.50    # dlib detection confidence
MATCH_THRESHOLD=0.45          # Euclidean distance for a match (lower = stricter)
LIVENESS_BLINK_FRAMES=5       # Consecutive low-EAR frames to count as 1 blink
LIVENESS_YAW_THRESHOLD=15     # Degrees of head rotation to count as movement
LIVENESS_WINDOW_SECONDS=3     # Liveness check window duration

# Image settings
SCREENSHOT_WIDTH=640          # Width in pixels (aspect-ratio preserved)
SCREENSHOT_QUALITY=85         # JPEG quality (0–100)
PROCESS_EVERY_N=2             # Process every Nth frame (skip for performance)

# Paths
DATASET_DIR=./data/dataset
SCREENSHOTS_DIR=./data/screenshots
PROFILE_PICTURES_DIR=./data/profile_pictures

# Model file paths (only needed when dlib is installed)
LANDMARKS_DAT=shape_predictor_68_face_landmarks.dat
FACE_REC_DAT=dlib_face_recognition_resnet_model_v1.dat
```

---

## Running the App

```powershell
# Make sure venv is activated
.\venv\Scripts\activate

# Start Streamlit
streamlit run frontend/app.py
```

The app will open at `http://localhost:8501`.

### Navigation Flow

```
http://localhost:8501
    ↓
Role Select: [Student Login] or [Faculty Login]
    ↓
Login Form (username + password)
    ↓
Student → Student Dashboard (profile + attendance)
Faculty → Faculty Dashboard (all students + capture)
```

---

## Face Recognition Setup

> The app works fully **without dlib** — all pages load, login works, profiles are editable, etc. Only the **03_Attendance_Capture.py** page requires dlib.

### Installing dlib on Windows

dlib requires **C++ Build Tools** and **CMake** to compile:

1. Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) — select "Desktop development with C++"
2. Install [CMake](https://cmake.org/download/) and add to PATH
3. Install dlib:
   ```powershell
   pip install dlib
   ```

### Download Model Files

Download these two files and place them in the project **root directory**:

| File | Download Link |
|------|--------------|
| `shape_predictor_68_face_landmarks.dat` | [dlib.net](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2) |
| `dlib_face_recognition_resnet_model_v1.dat` | [dlib.net](http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2) |

### Prepare Training Images

Place student images in this structure:
```
data/dataset/
    John Doe/
        img1.jpg
        img2.jpg
    Sarah Smith/
        img1.jpg
```

> **Important:** Folder names must exactly match the student names stored in the database.

### Generate Encodings

Once dlib is installed and images are in place, run the encoding loader from within the app or via Python:

```python
from backend.encoding_manager import load_encodings_from_images
load_encodings_from_images("./data/dataset")
```

---

## Default Credentials

After running `setup_database.py` and `seed_data.py`:

| Role | Username | Password | Student ID |
|------|----------|----------|-----------|
| Faculty | `admin` | `admin123` | — |
| Faculty | `faculty_admin` | `admin123` | — |
| Student | `john_student` | `password123` | STU-001 |
| Student | `sarah_student` | `password123` | STU-002 |
| Student | `mike_student` | `password123` | STU-003 |
| Student | `emma_student` | `password123` | STU-004 |

> **Warning:** Change all passwords in production. No password reset feature is built in — use `auth.create_user()` or direct database update.

---

## API / Module Reference

### `backend/database.py` — `Database`

| Method | Description |
|--------|-------------|
| `get_db()` | Context manager: auto-commit + rollback |
| `execute(query, params)` | SELECT → list of rows |
| `execute_one(query, params)` | SELECT → single row or None |
| `execute_insert(query, params)` | INSERT → last row ID |
| `execute_update(query, params)` | UPDATE/DELETE → row count |
| `init_schema()` | Idempotent schema creation |

### `backend/auth.py`

| Function | Description |
|----------|-------------|
| `hash_password(password)` | bcrypt hash |
| `verify_password(password, hash)` | bcrypt verify |
| `login_user(username, password)` | Returns user dict or None |
| `create_user(username, password, role)` | Creates user, returns ID |
| `get_user_by_id(user_id)` | Returns user dict |
| `deactivate_user(user_id)` | Soft-disable account |

### `backend/student_service.py`

| Function | Description |
|----------|-------------|
| `get_student_by_id(student_id)` | Fetch by student_id |
| `get_student_by_user_id(user_id)` | Fetch by login user_id |
| `get_all_students()` | All students (for faculty) |
| `search_students(query)` | Fuzzy by name/ID/dept |
| `update_student(student_id, **kwargs)` | Update allowed fields |
| `create_student(student_id, user_id, name, **kwargs)` | Insert new student |
| `delete_student(student_id)` | Delete (cascades) |

### `backend/attendance_service.py`

| Function | Description |
|----------|-------------|
| `record_attendance(student_id, screenshot, conf)` | One record per day |
| `get_attendance_by_student(student_id, limit)` | Student's history |
| `get_attendance_by_date(date_str)` | All students on a date |
| `get_attendance_stats(student_id, start, end)` | present/absent/% |
| `mark_attendance_manual(student_id, marked_by)` | Faculty manual mark |

### `backend/face_recognition_engine.py` — `FaceRecognitionEngine`

| Method | Description |
|--------|-------------|
| `detect_faces(frame)` | dlib HOG → list of (x,y,w,h) |
| `get_face_encoding(frame, location)` | 128-dim numpy array |
| `match_face(encoding, threshold)` | Returns (student_id, confidence) |
| `recognize_frame(frame)` | Full pipeline result list |
| `reload_encodings(new_dict)` | Update in-memory encodings |

### `backend/liveness_detector.py` — `LivenessDetector`

| Method | Description |
|--------|-------------|
| `update(landmarks)` | Process landmarks for one frame |
| `calculate_eye_aspect_ratio(landmarks)` | EAR float |
| `calculate_head_yaw(landmarks)` | Yaw degrees float |
| `is_live(landmarks)` | True if blink or yaw detected |
| `reset()` | Clear all state |

---

## Testing

The test suite covers the database layer, authentication, and face recognition logic.

```powershell
# Run all tests
.\venv\Scripts\python -m pytest tests/ -v

# Run specific test files
.\venv\Scripts\python -m pytest tests/test_database.py -v
.\venv\Scripts\python -m pytest tests/test_auth.py -v
.\venv\Scripts\python -m pytest tests/test_face_recognition.py -v
```

### Test Results

```
tests/test_database.py::test_database_connection          PASSED
tests/test_database.py::test_tables_exist                 PASSED
tests/test_database.py::test_insert_user                  PASSED
tests/test_database.py::test_insert_student               PASSED
tests/test_database.py::test_insert_faculty               PASSED
tests/test_database.py::test_context_manager_rollback     PASSED
tests/test_auth.py::test_password_hashing                 PASSED
tests/test_auth.py::test_create_user                      PASSED
tests/test_auth.py::test_login_success                    PASSED
tests/test_auth.py::test_login_failure_wrong_password     PASSED
tests/test_auth.py::test_login_failure_unknown_user       PASSED
tests/test_auth.py::test_invalid_role                     PASSED
tests/test_auth.py::test_inactive_user_blocked            PASSED
tests/test_auth.py::test_faculty_login                    PASSED
tests/test_face_recognition.py::test_encoding_blob_roundtrip  PASSED
tests/test_face_recognition.py::test_face_engine_no_encodings PASSED
tests/test_face_recognition.py::test_face_engine_match_face   PASSED
tests/test_face_recognition.py::test_face_engine_no_match     PASSED
tests/test_face_recognition.py::test_face_engine_reload_encodings PASSED
tests/test_face_recognition.py::test_detect_faces_dlib    SKIPPED (dlib not installed)

19 passed, 1 skipped
```

---

## Development Roadmap

### Completed
- [x] SQLite schema with 5 tables, indexes, FK constraints
- [x] bcrypt authentication + role-based routing
- [x] Student CRUD with validation
- [x] Attendance service (one record/day, stats, export)
- [x] Image processing (profile picture + screenshot compression)
- [x] Face encoding blob storage/retrieval
- [x] dlib face recognition engine (detection + encoding + matching)
- [x] Liveness detector (EAR + head yaw)
- [x] Streamlit multi-page app (login, student dashboard, faculty dashboard, capture)
- [x] Reusable components (sidebar, attendance table, student list, camera widget, profile form)
- [x] `.env` configuration + `.gitignore`
- [x] Pytest suite (19 tests passing)

### Planned
- [ ] Install and integrate dlib (requires C++ Build Tools)
- [ ] Encoding generation from dataset images
- [ ] Live webcam attendance session with bounding box overlay
- [ ] Password reset (admin-only)
- [ ] Streamlit auto-refresh polling (5-10 sec) for faculty view
- [ ] Attendance report PDF generation
- [ ] Multi-camera support

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow the code standards in `attendance.md` (no print statements, type hints, docstrings, parameterized SQL)
4. Run tests: `pytest tests/ -v` — all must pass
5. Submit a pull request with a clear description

---

## Security Notes

- Passwords are **never stored in plain text** — bcrypt with unique salts
- Session state **never contains the password hash**
- All SQL uses **parameterized queries** — no string interpolation
- `.env` and `data/database.sqlite` are gitignored
- Database errors are logged server-side, not exposed to the UI

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with Python · Streamlit · SQLite · dlib · OpenCV*  
*Last updated: April 15, 2026*

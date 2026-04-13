# Face Recognition Attendance System

**Status: Production Ready (MVP ✅)**

A robust, real-time face recognition system that tracks attendance with visual feedback, stability confirmation, and Excel export. Built with `face_recognition`, OpenCV, and multi-frame validation for accuracy.

---

## 🎯 Key Features

- ✅ **Real-time Face Recognition** – Identifies people from webcam feed
- ✅ **Stability Verification** – Requires N consecutive frames to confirm identity (prevents false positives)
- ✅ **Automatic Attendance Marking** – Logs timestamp and date to CSV
- ✅ **Excel Export** – Formatted reports with styled headers and borders
- ✅ **Visual Feedback** – Green boxes for confirmed, orange for unknown faces
- ✅ **Status Display** – Live list of marked attendees
- ✅ **Reset Capability** – Clear session data and restart detection (Press R)
- ✅ **Performance Optimization** – Configurable frame skipping and resizing
- ✅ **Robust Error Handling** – Graceful handling of missing images, no faces detected, etc.

---

## 📁 Folder Structure

```
scratch/
├── attendance_system.py   ← main script
├── requirements.txt
├── attendance.csv         ← auto-created (CSV log)
├── attendance.xlsx        ← generated on Excel export
├── dataset/               ← REQUIRED training dataset
│   ├── Debnil/
│   ├── Jyotirmoy/
│   ├── Kaustav/
│   └── Soumita/
└── test_*.py              ← (development/testing)
```

---

## ⚙️ Setup

### 1. Python Version

**Use Python 3.10** (or 3.9-3.11). Python 3.12+ requires manual compilation of `dlib`, which is complex on Windows.

```bash
# Verify Python 3.10 is installed
py -3.10 --version
```

### 2. Install Dependencies

```bash
# Via pip
pip install -r requirements.txt
```

**OR manually:**
```bash
pip install face_recognition==1.3.0 opencv-python==4.8.1.78 numpy==1.26.4 openpyxl==3.1.5
```

✅ **All dependencies have pre-built wheels** – no compilation needed.

### 3. Prepare Dataset

Create a `dataset/` folder with this structure:
```
dataset/
    person_name/
        image1.jpg
        image2.jpg
        image3.jpg
```

- **Folder name** → Person's name (will appear in attendance)
- **Images per person** → 1–3 clear, frontal face photos recommended
- **Format** → JPG, PNG, or JPEG
- **Quality** → Good lighting, clear faces (blurry images won't encode)

### 4. Run the System

```bash
python attendance_system.py
```

---

## 🚀 Usage

### Main Menu
```
1. Run face recognition (default)
2. Export attendance to Excel
```

### Controls
| Key | Action |
|-----|--------|
| **Q** | Quit application |
| **R** | Reset: Clear attendance CSV and start fresh |

### First Run Example

1. Start the app → launches webcam
2. Face detected → **Orange box** (building confidence)
3. After ~10 consecutive frames → **Green box** (confirmed)
4. Attendance marked for that person → **Brief notification**
5. Timestamp + date logged to `attendance.csv`
6. Press **Q** to exit or **R** to reset

## 🔧 Configuration

All settings are in `attendance_system.py` (top of file):

| Variable        | Default | Description                                      |
|-----------------|---------|--------------------------------------------------|
| `DATASET_DIR`   | `dataset` | Path to dataset folder                           |
| `ATTENDANCE_FILE` | `attendance.csv` | Output CSV file                        |
| `MATCH_THRESHOLD` | `0.48`  | Face distance threshold (lower = stricter)       |
| `CONFIRM_FRAMES`  | `10`    | Consecutive frames before confirming identity    |
| `PROCESS_EVERY_N` | `2`     | Process every Nth frame (for performance)        |

### Tuning Tips

**More false positives?** → Lower `MATCH_THRESHOLD` (e.g., `0.40`)  
**More false negatives?** → Raise `MATCH_THRESHOLD` (e.g., `0.55`)  
**Too many false detections?** → Increase `CONFIRM_FRAMES` (e.g., `15`)  
**Laggy video?** → Increase `PROCESS_EVERY_N` (e.g., `3` or `4`)  
**Slow recognition?** → Increase `MATCH_THRESHOLD` slightly

---

## � Output Files

### `attendance.csv`
```
Name,Time,Date
Kaustav,09:32:11,2026-04-13
Jyotirmoy,09:45:03,2026-04-13
Debnil,10:15:22,2026-04-13
```

### `attendance.xlsx` (Excel Export)
Generated via menu option 2. Includes:
- Header row with blue background and white text
- Bordered cells, centered alignment
- Auto-adjusted column widths

---

## 🎨 UI Legend

| Indicator | Meaning |
|-----------|---------|
| 🟢 **Green Box + Name** | Identity confirmed, attendance marked |
| 🟠 **Orange Box + "Unknown"** | Face detected but unknown or building confidence |
| **Status Bar** | Shows all attendees marked today |
| **Notification** | Brief confirmation when attendance is recorded |

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| **No face detected in webcam** | Check lighting, position face clearly in frame, ensure camera is not blocked |
| **Person recognized but box stays orange** | Increase `CONFIRM_FRAMES`; ensure dataset images are clear and well-lit |
| **Wrong person identified** | Lower `MATCH_THRESHOLD` (e.g., 0.40); add more diverse images to dataset |
| **Same person marked twice** | Confidence detection is working; press **R** to reset if needed |
| **Webcam not found** | Change `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)` in code |
| **Installation fails (Windows)** | Use **Python 3.10** (3.12+ requires manual dlib compilation) |
| **"No face found" warnings** | Check images in dataset folder – replace blurry or angled photos |
| **Excel export fails** | Ensure `openpyxl` is installed: `pip install openpyxl` |
| **System crashes on startup** | Verify dataset folder exists and has valid image files |
| **CSV file locked (Windows)** | Close Excel before running the system again |

---

## 🏗️ How It Works

1. **Dataset Loading** → Encodes all faces from `dataset/` folders into embeddings
2. **Webcam Capture** → Grabs frames from camera (every Nth frame for speed)
3. **Face Detection** → Locates faces in the frame using HOG model
4. **Face Encoding** → Converts detected face to 128-D embedding
5. **Face Matching** → Compares against known encodings using Euclidean distance
6. **Stability Tracking** → Confirms identity only after N consecutive matching frames
7. **Attendance Mark** → Logs confirmed person with timestamp to CSV
8. **Excel Export** → Converts CSV to formatted spreadsheet (optional)

---

## 🔬 Technical Stack

| Component | Library | Version |
|-----------|---------|---------|
| Face Detection/Encoding | `face_recognition` | 1.3.0 |
| Image Processing | `opencv-python` | 4.8.1.78 |
| Numerical Computing | `numpy` | 1.26.4 |
| Excel Output | `openpyxl` | 3.1.5 |

---

## 📋 Requirements

- **Python 3.9–3.11** (3.10 recommended; 3.12+ not supported due to dlib)
- **Webcam** connected and accessible
- **Dataset folder** with person subfolders containing face images
- **Windows/Linux/macOS** (tested on Windows 10+)

---

## 🚀 Future Enhancements

Potential improvements for future versions:
- Multi-face recognition (detect multiple people simultaneously)
- Database backend (SQLite/PostgreSQL instead of CSV)
- Real-time analytics dashboard
- REST API for integration with other systems
- Cloud-based face encodings storage
- Attendance statistics and reporting
- Mobile app support

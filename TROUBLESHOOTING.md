# TROUBLESHOOTING CHECKLIST

## Pre-Testing Setup

### ✅ Step 1: Database Health Check
```bash
python verify_attendance_saved.py
```

**Look for**:
- ✅ Database file exists
- ✅ 4 students registered (Debnil, Jyotirmoy, Kaustav, Soumita)
- ✅ No errors printed

**If fails**: Database might be corrupted, run:
```bash
python setup_database.py
python seed_data.py
```

---

### ✅ Step 2: Verify Video System Works
```bash
python attendance_system.py
```

**Look for in console**:
```
[CONFIG] Database path: c:\...\data\database.sqlite
[CONFIG] Dataset directory: c:\...\dataset
[INFO] Opened camera 0
[INFO] Dataset ready – X encoding(s) for X person(s)
```

**If not showing**: Camera might not be working or dataset not found

---

### ✅ Step 3: Check Dataset Folders
Verify these exist with face images:
- `dataset/Debnil/` - Should have at least 1 image
- `dataset/Jyotirmoy/` - Should have at least 1 image
- `dataset/Kaustav/` - Should have at least 1 image
- `dataset/Soumita/` - Should have at least 1 image

**If missing**: Add face images for each person

---

### ✅ Step 4: Test Attendance Recording
1. Run: `python attendance_system.py`
2. Look at camera for 10+ frames
3. When face is recognized, console should show:
   ```
   [ATTENDANCE] ✓ Kaustav marked at HH:MM:SS on 2026-04-16
   [DB] ✓ Attendance saved for kaustav (STU-003) with confidence XX.X%
   ```

**If [DB] line missing**: Database save failed, check "Debugging Database Saves" below

---

### ✅ Step 5: Verify Database Has Records
```bash
python verify_attendance_saved.py
```

**Should show**:
```
TODAY'S ATTENDANCE (2026-04-16):
  ✅ Found X attendance record(s):
    Record 1:
      Student: Kaustav (STU-003)
      ...
```

**If shows ❌ NO ATTENDANCE RECORDS**: Jump to "Debugging Database Saves"

---

### ✅ Step 6: Start Frontend
```bash
streamlit run frontend/app.py
```

**Verify**:
- Opens at `http://localhost:8501`
- Can login as faculty (admin123 / admin100)
- Page loads without errors

---

### ✅ Step 7: Check Attendance Display
1. Login as faculty
2. Go to "📊 Attendance Records"
3. Select "📅 Today" tab
4. **Should see** attendance records within 5 seconds

**If not showing**:
- Click "🔄 Refresh Now" button
- If still not showing → "Debugging Frontend Display" below

---

## Debugging Database Saves

### If `[DB] ✓ Attendance saved` is NOT showing

**Step A**: Check console for `[ERROR]` messages
```
Look for lines starting with [ERROR]
```

**Step B**: Explicitly test save function
```bash
# Run this Python code:
python -c "
from backend.attendance_service import record_attendance
result = record_attendance(
    student_id='STU-003',
    screenshot_path='/tmp/test.jpg',
    confidence=95.0,
    marked_by='test'
)
print(f'Save result: {result}')
"
```
Should print: `Save result: True` or `Save result: False`

**Step C**: Check database permissions
```bash
# Verify database file exists and is readable
ls -la data/database.sqlite
```
Should show a file (size > 0 KB)

**Step D**: Check student name matching
```bash
# Verify "Kaustav" (from folder) matches database
python verify_attendance_saved.py | grep -i kaustav
```
Should show: `STU-003         Kaustav`

---

## Debugging Frontend Display

### If attendance not showing in frontend

**Step A**: Verify data is in database
```bash
python verify_attendance_saved.py
```
Must show ✅ records for today

**Step B**: Check frontend logs
Look at Streamlit console for errors
Should NOT see any red error text

**Step C**: Force refresh
- Click "🔄 Refresh Now" button
- If data appears → Working! (just was cached)
- If data doesn't appear → Check Step D

**Step D**: Test frontend database connection
```bash
# Add this to frontend/pages/04_Attendance_Records.py temporarily:
import sys
sys.path.insert(0, "..")
from backend.database import db
rows = db.execute("SELECT COUNT(*) as cnt FROM attendance WHERE date = date('now')")
print(f"Attendance records today: {rows[0]['cnt']}")
```

---

## Common Issues & Fixes

### Issue: "Database is locked"
**Solution**: 
1. Stop all applications (video system, frontend)
2. Wait 5 seconds
3. Delete `data/database.sqlite-wal` and `data/database.sqlite-shm` files
4. Restart system

### Issue: "Camera not opening"
**Solution**:
1. Check camera is connected: `ls /dev/video*` (Linux) or Device Manager (Windows)
2. Try: `python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"`
3. Should print `True`

### Issue: "No face detected"
**Solution**:
1. Ensure good lighting
2. Face should be clearly visible
3. Try face with different angles
4. Increase `CONFIRM_FRAMES` in attendance_system.py if too sensitive

### Issue: "Student not found"
**Solution**:
1. Dataset folder name MUST match database name exactly
2. ✅ Correct: `dataset/Kaustav/` matches "Kaustav" in database
3. ❌ Wrong: `dataset/kaustav/` won't match "Kaustav"
4. Fix: Rename folder to match case

### Issue: "Screenshot path not saved"
**Solution**:
1. Ensure `screenshots/` folder exists
2. Run: `mkdir screenshots` if missing
3. Check folder has write permissions

---

## Performance Tuning (Optional)

### If system is slow

**In `attendance_system.py`**:
- Increase `PROCESS_EVERY_N = 3` (process every 3rd frame instead of 2nd)
- Decrease `MATCH_THRESHOLD = 0.45` (relaxes face matching)
- Increase `CONFIRM_FRAMES = 15` (waits longer for confirmation)

### If frontend is slow

**In `frontend/pages/04_Attendance_Records.py`**:
- Increase `refresh_interval = 10` (refresh every 10 seconds instead of 5)
- Or reduce with: `refresh_interval = 2` (refresh every 2 seconds for real-time)

---

## Quick Self-Tests

### Test 1: Database Connection
```bash
python -c "from backend.database import db; print('✅ DB OK' if db.db_path else '❌ DB FAIL')"
```

### Test 2: Student Lookup
```bash
python -c "from attendance_system import get_student_id_by_name; print(get_student_id_by_name('kaustav'))"
```
Should print: `STU-003`

### Test 3: Attendance Save
```bash
python verify_attendance_saved.py | grep -c "REGISTERED STUDENTS"
```
Should print: `1` (means section found)

---

## When to Restart Everything

**Restart scenario**:
1. Made changes to database
2. Changed dataset folder names
3. Getting "database locked" errors
4. Frontend shows old data

**How to restart**:
```bash
# Stop all terminal windows

# Step 1: Clean up
rm data/database.sqlite data/database.sqlite-wal data/database.sqlite-shm

# Step 2: Recreate database
python setup_database.py
python seed_data.py

# Step 3: Verify
python verify_attendance_saved.py

# Step 4: Restart applications
python attendance_system.py  # Terminal 1
streamlit run frontend/app.py  # Terminal 2
```

---

## Getting Help

If still stuck, collect this info:

1. Output of `python verify_attendance_saved.py`
2. Console output when recording attendance
3. Screenshot of frontend showing issue
4. Any `[ERROR]` messages printed
5. What OS you're on (Windows/Mac/Linux)

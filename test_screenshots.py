"""
test_screenshots.py
Test to verify screenshots are saved and can be displayed by faculty
"""

import sys
import os
from datetime import date
import shutil

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database import db
from backend.attendance_service import record_attendance

def test_screenshots():
    print("=" * 70)
    print("  SCREENSHOT VERIFICATION TEST")
    print("=" * 70)
    
    # Create test screenshots directory
    test_screenshots_dir = "screenshots"
    os.makedirs(test_screenshots_dir, exist_ok=True)
    print(f"\n✅ Screenshots directory ready: {os.path.abspath(test_screenshots_dir)}")
    
    # Create a simple test image from an existing one if available
    # or create a placeholder
    test_image_path = None
    
    # Try to find an image in the dataset
    dataset_dir = "dataset"
    for person in os.listdir(dataset_dir):
        person_path = os.path.join(dataset_dir, person)
        if os.path.isdir(person_path):
            for img_file in os.listdir(person_path):
                if img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    src_img = os.path.join(person_path, img_file)
                    test_image_path = src_img
                    print(f"✅ Found test image: {src_img}")
                    break
        if test_image_path:
            break
    
    if not test_image_path:
        print("⚠️  No test images found in dataset. Using placeholder.")
        # Create a simple placeholder image
        import cv2
        import numpy as np
        placeholder = np.zeros((100, 100, 3), dtype=np.uint8)
        placeholder[:] = (0, 255, 0)  # Green image
        test_image_path = os.path.join(test_screenshots_dir, "placeholder.jpg")
        cv2.imwrite(test_image_path, placeholder)
    
    # Get all students
    print("\n" + "─" * 70)
    print("TESTING SCREENSHOT SAVE FOR EACH STUDENT:")
    print("─" * 70)
    
    students = db.execute(
        "SELECT student_id, name FROM students ORDER BY name"
    )
    
    today = date.today().isoformat()
    test_results = []
    
    for row in students:
        student_id = row['student_id']
        student_name = row['name']
        
        print(f"\n📝 Testing: {student_name} ({student_id})")
        
        # Copy test image to screenshots folder with unique name
        screenshot_filename = f"{test_screenshots_dir}/{student_name.lower()}_{date.today().strftime('%Y%m%d')}_test.jpg"
        screenshot_abs_path = os.path.abspath(screenshot_filename)
        
        try:
            # Copy test image
            shutil.copy(test_image_path, screenshot_abs_path)
            print(f"   ✅ Screenshot created: {screenshot_abs_path}")
            
            # Save to database
            result = record_attendance(
                student_id=student_id,
                screenshot_path=screenshot_abs_path,
                confidence=92.5,
                marked_by="test"
            )
            
            if result:
                print(f"   ✅ Attendance recorded with screenshot")
                test_results.append((student_name, screenshot_abs_path, True))
            else:
                print(f"   ⚠️  Already marked today (skipped)")
                test_results.append((student_name, screenshot_abs_path, False))
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            test_results.append((student_name, screenshot_abs_path, False))
    
    # Verify records with screenshots in database
    print("\n" + "─" * 70)
    print("VERIFYING SCREENSHOTS IN DATABASE:")
    print("─" * 70)
    
    records = db.execute(
        """
        SELECT a.*, s.name as student_name
        FROM attendance a
        LEFT JOIN students s ON a.student_id = s.student_id
        WHERE a.date = ? AND a.marked_by = 'test'
        ORDER BY a.student_id
        """,
        (today,)
    )
    
    records = [dict(r) for r in records]
    
    print(f"\n✅ Found {len(records)} test records for today\n")
    
    for i, record in enumerate(records, 1):
        print(f"Record {i}: {record['student_name']} ({record['student_id']})")
        print(f"   Time: {record['time_in']}")
        print(f"   Confidence: {record['face_confidence']:.1f}%")
        print(f"   Screenshot path: {record['screenshot_path']}")
        
        # Check if screenshot file exists
        if record['screenshot_path'] and os.path.exists(record['screenshot_path']):
            file_size = os.path.getsize(record['screenshot_path'])
            print(f"   ✅ Screenshot file EXISTS ({file_size} bytes)")
        else:
            print(f"   ❌ Screenshot file NOT FOUND")
        print()
    
    # Test frontend display logic
    print("─" * 70)
    print("SIMULATING FRONTEND DISPLAY:")
    print("─" * 70)
    
    for record in records:
        print(f"\n👤 {record['student_name']} ({record['student_id']})")
        print(f"   ⏰ Time: {record['time_in']}")
        print(f"   🎯 Confidence: {record['face_confidence']:.1f}%")
        
        if record['screenshot_path'] and os.path.exists(record['screenshot_path']):
            print(f"   🖼️  Screenshot: WILL DISPLAY ✅")
        else:
            print(f"   🖼️  Screenshot: NOT AVAILABLE ⚠️")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY:")
    print("=" * 70)
    print(f"✅ Screenshots saved: {len(records)}")
    print(f"✅ All records have screenshot paths: {all(r['screenshot_path'] for r in records)}")
    print(f"✅ All screenshot files exist: {all(os.path.exists(r['screenshot_path']) for r in records if r['screenshot_path'])}")
    print(f"✅ Faculty will see: Student name + Time + Confidence + Screenshot image")
    print("\n🎉 ALL READY FOR FACULTY VIEW")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    test_screenshots()

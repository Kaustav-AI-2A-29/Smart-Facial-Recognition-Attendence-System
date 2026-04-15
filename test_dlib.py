import face_recognition
import cv2
import numpy as np
from PIL import Image
import os

# FIX 7: Auto-discover first available image from dataset directory
DATASET_DIR = "dataset"
IMAGE_PATH = None

for person_dir in os.listdir(DATASET_DIR):
    person_path = os.path.join(DATASET_DIR, person_dir)
    if os.path.isdir(person_path):
        for filename in os.listdir(person_path):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                IMAGE_PATH = os.path.join(person_path, filename)
                break
        if IMAGE_PATH:
            break

if not IMAGE_PATH:
    print("[ERROR] No images found in dataset directory!")
    exit(1)

print(f"Using image: {IMAGE_PATH}")
print("=" * 50)

print("=== Test 1: Original load_image_file ===")
image = face_recognition.load_image_file(IMAGE_PATH)
print(f'Shape: {image.shape}, dtype: {image.dtype}')
print(f'Type: {type(image)}, flags: C_CONTIG={image.flags["C_CONTIGUOUS"]}, F_CONTIG={image.flags["F_CONTIGUOUS"]}')

print("\n=== Test 2: PIL/Pillow ===")
pil_image = Image.open(IMAGE_PATH).convert('RGB')
np_image = np.array(pil_image)
print(f'Shape: {np_image.shape}, dtype: {np_image.dtype}')
print(f'Type: {type(np_image)}, flags: C_CONTIG={np_image.flags["C_CONTIGUOUS"]}, F_CONTIG={np_image.flags["F_CONTIGUOUS"]}')
try:
    face_locations = face_recognition.face_locations(np_image, model='hog')
    print(f'Success! Found {len(face_locations)} faces')
except Exception as e:
    print(f'Error: {e}')

print("\n=== Test 3: cv2.imread ===")
cv2_image = cv2.imread(IMAGE_PATH)
cv2_image_rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
print(f'Shape: {cv2_image_rgb.shape}, dtype: {cv2_image_rgb.dtype}')
print(f'Type: {type(cv2_image_rgb)}, flags: C_CONTIG={cv2_image_rgb.flags["C_CONTIGUOUS"]}, F_CONTIG={cv2_image_rgb.flags["F_CONTIGUOUS"]}')
try:
    face_locations = face_recognition.face_locations(cv2_image_rgb, model='hog')
    print(f'Success! Found {len(face_locations)} faces')
except Exception as e:
    print(f'Error: {e}')

print("\n=== Test 4: Copy to new memory ===")
image_copy = np.ascontiguousarray(image)
print(f'Copy shape: {image_copy.shape}, dtype: {image_copy.dtype}')
try:
    face_locations = face_recognition.face_locations(image_copy, model='hog')
    print(f'Success! Found {len(face_locations)} faces')
except Exception as e:
    print(f'Error: {e}')

import dlib
import numpy as np

# Test dlib directly without face_recognition wrapper
print("Testing dlib with dlib's own image loading...")

try:
    # Load using dlib's function
    print("Trying dlib.load_rgb_image...")
    dlib_image = dlib.load_rgb_image('dataset/Debnil/photo1.jpeg')
    print(f'Image type (from dlib): {type(dlib_image)}')
    
    # Try dlib's face detector
    detector = dlib.get_frontal_face_detector()
    faces = detector(dlib_image, 1)
    print(f'Success! Found {len(faces)} faces')
    
    # Now try converting to numpy and passing back
    dlib_array = np.asarray(dlib_image)
    print(f'\nBack to numpy: shape={dlib_array.shape}, dtype={dlib_array.dtype}')
    faces2 = detector(dlib_array, 1)
    print(f'Found {len(faces2)} faces with numpy array')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

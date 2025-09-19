import re
import random
import string
import io
import numpy as np
from PIL import Image

# FALL BACK TO STUB FOR JUST TONIGHT WHILE I SETUP SOMETH ELSE!
try:
    import face_recognition as fr
    FACE_ENABLED = True
except Exception:
    fr = None
    FACE_ENABLED = False

def bytes_to_encoding(image_bytes: bytes):
    """
    Convert a JPEG/PNG bytes blob (from webcam) into a 128-d face embedding.
    Returns None if no *single* face is found or FACE is disabled.
    """
    if not FACE_ENABLED or fr is None:
        return None
    try:
        im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return None
    arr = np.array(im)
    try:
        # You can switch to model="cnn" if you’ve compiled dlib with CUDA.
        locs = fr.face_locations(arr, model="hog")
        if len(locs) != 1:
            return None
        encs = fr.face_encodings(arr, known_face_locations=locs)
        if len(encs) != 1:
            return None
        return encs[0]
    except Exception:
        return None

def face_distance(a, b) -> float:
    """
    Euclidean distance between two embeddings.
    face_recognition considers ~0.6 a common threshold.
    """
    a = np.asarray(a); b = np.asarray(b)
    return float(np.linalg.norm(a - b))

def image_to_encoding(img_path: str):
    try:
        img = fr.load_image_file(img_path)
    except FileNotFoundError:
        return None
    
    face_encodings = fr.face_encodings(img)

    if len(face_encodings) == 0:
        return None

    return face_encodings[0]

def is_valid_email(email: str) -> bool:
    # This is a simple regular expression for emails. 
    email_regex = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    
    if len(email) > 255:
        return False

    if re.match(email_regex, email):
        return True
    return False

def generate_class_code():
        class_code = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
        return class_code
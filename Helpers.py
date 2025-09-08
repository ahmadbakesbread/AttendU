import re
import random
import string

# FALL BACK TO STUB FOR JUST TONIGHT WHILE I SETUP SOMETH ELSE!
try:
    import face_recognition as fr
    FACE_ENABLED = True
except Exception:
    fr = None
    FACE_ENABLED = False

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
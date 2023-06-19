import face_recognition as fr
import re

def image_to_encoding(img_path: str):
    try:
        img = fr.load_image_file("./images/" + img_path)
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
import face_recognition as fr

def image_to_encoding(img_path: str):
    try:
        img = fr.load_image_file("./images/" + img_path)
    except FileNotFoundError:
        return None
    
    face_encodings = fr.face_encodings(img)

    if len(face_encodings) == 0:
        return None

    return face_encodings[0]


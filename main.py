import face_recognition
import cv2 
import time
from DatabaseManager import DatabaseManager

def main():
    """
    The function main() is responsible for setting up the database and main loop (while True) 
    that captures and procceses the video frame.

    Additionally, the program detects student faces, performs facial recognition comparisons, 
    and display the results in real-time.

    The student must be continously recognized for at least 4 seconds by the program in order
    to confirm their identity.
    """
    with DatabaseManager() as db_manager:
        db_manager.initialize_database()
        db_manager.add_student('2456248501', 'Lebron James', 'lebron.jpg') # New student added to the database

        video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW) # Captures Video & Makes Camera Setup Faster

        start_time = None
        last_seen_student = None
        continous_recognition = False

        while True:
            
            ret, frame = video_capture.read()

            face_locations = face_recognition.face_locations(frame)  # Detects the locations of faces in the frame using face_recognition library
            face_encodings = face_recognition.face_encodings(frame, face_locations)  # Computes the encodings of the faces in the given frame

            color = (0, 0, 255) # Red color box for unknown face
            name = "Unknown" 

            if not face_encodings:  # If no faces are detected, reset the timer and the last seen student
                start_time = None
                last_seen_student = None
                continous_recognition = False
            else:
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    identification_result = db_manager.identify_student(face_encoding)
                    
                    if identification_result['status'] == 'success':  # Conditon checks if student in the frame is recognized based on the face encodings in the database
                        student_name = identification_result['student_name']
                        student_number = identification_result['student_number']
                        if last_seen_student == student_number:  # Condition Compares Student With The Last Seen Student
                            if start_time and time.time() - start_time >= 4:  # Condition checks if the student has been continously recognized for at least 4 seconds
                                continous_recognition = True  # If all conditions are met, set the value of continous_recognition to True

                        else:  # If a new student is recognized, reset the timer
                            start_time = time.time()  
                            last_seen_student = student_number
                            continous_recognition = False

                    if continous_recognition: 
                        color = (0, 255, 0) # Draw green colored box when face is recognized
                        name = f"{student_name}, {student_number}" # Student name and number will be listed under the box
                        
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)  # The box around the student's face will be green if recognized, and red otherwise
                    cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)  # The student's name and number will be listed under the box if recognized, and listed as "Unkown" Otherwise 
            
            # Display the resulting image
            cv2.imshow('StudentWebcam', frame)

            # Exit loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):  # Kill the prorgam by pressing the 'q' key
                break

        # Release the capture when done
        video_capture.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
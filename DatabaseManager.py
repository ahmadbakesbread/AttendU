from __future__ import annotations
import pickle
import face_recognition as fr
import csv
import pyodbc
from typing import Dict, Optional, Union
from numpy import ndarray
import configparser


class DatabaseManager:
    """
    Manages the connection and operations with a MySQL database for student information and face encodings.

    === Usage Example ===
        with DatabaseManager() as db_manager:
            db_manager.initialize_database()
            db_manager.add_student('2398021322', 'Lebron James', 'lebron.jpg')
            db_manager.identify_student(face_encoding)

    === Private Attributes ===
        _db_name (str): The name of the MySQL database.
        _connection (pyodbc.Connection): The connection object for the MySQL database.
        _cursor (pyodbc.Cursor): The cursor object for executing SQL queries.
    """
    def __init__(self) -> None:
        """
        Initializes an instance of the DatabaseManager class by establishing a connection
        to the database.

        Raises:
            Exception: If a connection to the database cannot be established.
        """
        config = configparser.ConfigParser()
        config.read('config.ini')
        self._db_name = config['DATABASE']['db_name']
        self._connection = self._create_connection()
        try:
            self._cursor = self._connection.cursor()
        except pyodbc.Error as e:
            raise Exception(f"Error creating cursor: {str(e)}")
    
    def _create_connection(self) -> Optional[pyodbc.Connection]:
        """
        Establishes a connection to the MySQL database using a specified configuration.

        Returns:
            Connection to the MySQL database or None if a connection could not be established.

        Raises:
            Exception: If a connection to the database cannot be established.
        """
        config = configparser.ConfigParser()
        config.read('config.ini')

        username = config['DATABASE']['username']
        password = config['DATABASE']['password']
        driver = config['DATABASE']['driver']
        hostname = config['DATABASE']['host']
        connection_string = f"DRIVER={{{driver}}};SERVER={hostname};DATABASE={self._db_name};UID={username};PWD={password}"
        try:
            return pyodbc.connect(connection_string)
        except pyodbc.Error as e:
            raise Exception(f"Error connecting to the database: {str(e)}")
    
    def close_connection(self) -> dict:
        """
        Closes the cursor and connection to the database.

        Raises:
            dict: Dictionary containing the 'status', 'message', and 'code'.
        """
        try:
            self._cursor.close()
        except Exception as e:
            return {"status": "error", "message": f"Error occurred while closing cursor: {str(e)}", "code": 500}
        
        try:
            self._connection.close()
        except Exception as e:
            return {"status": "error", "message": f"Error occurred while closing connection: {str(e)}", "code": 500}
        
        return {"status": "success", "message": "Database connection successfully closed.", "code": 200}
    
    def __enter__(self) -> DatabaseManager:
        """
        Re-establishes the database connection and returns the DatabaseManager instance.
        This method is automatically called when the 'with' statement is used.

        Returns:
            self: The current instance of DatabaseManager.
        
        Raises:
            Exception: If a connection to the database cannot be established.
        """
        config = configparser.ConfigParser()
        config.read('config.ini')
        self._db_name = config['DATABASE']['db_name']
        self._connection = self._create_connection()
        try:
            self._cursor = self._connection.cursor()
        except pyodbc.Error as e:
            raise Exception(f"Error creating cursor: {str(e)}")
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> dict:
        """
        Closes the connection to the database. This method is automatically called 
        when exiting the 'with' statement, even if an error was raised within the 'with' block.

        Parameters:
            exc_type: The type of the exception that caused the context to be exited, if any.
            exc_value: The instance of the exception that caused the context to be exited, if any.
            traceback: A traceback object encapsulating the call stack at the point 
                    where the exception originally occurred, if any.
        """
        return self.close_connection()

    def initialize_database(self) -> dict:
        """
        Initializes the specified database, removing all existing student data
        and repopulates it using the data from the student_info.csv file. 

        Returns:
            dict: Dictionary containing the 'status', 'message', and 'code'.
        """
        errors = []
        # Resetting (emptying) the database. 
        try :
            self._cursor.execute(f"DELETE FROM {self._db_name}.students")  
        except pyodbc.Error as e:
            return {"status": "failed", "message": f"Error occurred while attempting to delete from the database: {e}", "code": 500, "errors": errors}

        # Reading student info from CSV file.
        try:
            with open('./student_info.csv', 'r') as csv_f:
                f_reader = csv.reader(csv_f)
                next(f_reader)  # Skips the header.

                for row in f_reader:
                    student_number = row[0]
                    student_name = row[1]
                    img_path = row[2]

                    try:
                        img = fr.load_image_file("./images/" + img_path)
                    except FileNotFoundError:
                        errors.append({"status": "failed", "message": f"Image {img_path} not found.", "code": 404})
                        continue
                    
                    # Computing the face encoding from the student image.
                    face_encoding = fr.face_encodings(img)

                    # If face encoding computation is successful, serialize it and store it in the database.
                    if len(face_encoding) > 0:  
                        serial_face_encoding = pickle.dumps(face_encoding[0])  
                        query = f"INSERT INTO {self._db_name}.students (student_id, full_name, face_encoding) VALUES (?, ?, ?)"
                        try:
                            self._cursor.execute(query, (student_number, student_name, serial_face_encoding))
                        except pyodbc.Error as e:
                            errors.append({"status": "failed", "message": f"Error occurred while attempting to insert {student_number} into the database: {e}", "code": 500})
                            continue
        
        except FileNotFoundError:
            return {"status": "failed", "message": "CSV file not found.", "code": 404, "errors": errors}
        except Exception as e:
            return {"status": "failed", "message": f"Something went wrong: {e}", "code": 500, "errors": errors}
        
        self._connection.commit()

        if errors:
            return {"status": "partial", "message": "Database was partially initialized.", "code": 206, "errors": errors}

        return {"status": "success", "message": "Database was successfully initialized.", "code": 200}
    
    def add_student(self, student_number: str, student_name: str, img_path: str) -> bool:
        """
        Adds the specified student's information into the given database.

        Parameters:
            student_number (str): The ID number of the student.
            student_name (str): The name of the student.
            img_path (str): Path to the image of the student.

        Returns:
            dict: Dictionary containing the 'status', 'message', and 'code'.
        """
        try:
            img = fr.load_image_file("./images/" + img_path)
        except FileNotFoundError:
            return {"status": "error", "message": f"{img_path} not found for student {student_name}.", "code": 404}
        
        face_encodings = fr.face_encodings(img)

        if len(face_encodings) == 0:
            return {"status": "error", "message": f"No face encoding found for student {student_number}.", "code": 400}
        face_encoding = face_encodings[0]

        if len(face_encoding) > 0:
            serial_face_encoding = pickle.dumps(face_encoding)      
            query = f"INSERT INTO {self._db_name}.students (student_id, full_name, face_encoding) VALUES (?, ?, ?)"
            try:
                self._cursor.execute(query, (student_number, student_name, serial_face_encoding))
            except pyodbc.Error as e:
                return {"status": "error", "message": f"Error occurred while attempting to insert {student_number} into the database: {str(e)}", "code": 500}
        
        self._connection.commit()
        return {"status": "success", "message": f"Successfully added student {student_name} to the database.", "code": 200}
    
    def identify_student(self, student_face_encoding: ndarray, tolerance: float = 0.6) -> Dict[str, Union[str, int, None]]:
        """
        Retrieves the student's information from the database by comparing the provided face encoding 
        with the ones stored in the database. The face encoding comparison is done within the given tolerance.

        Parameters:
            student_face_encoding (np.ndarray): The face encoding of the student to match.
            tolerance (float, optional): Tolerance for face comparison. Lower values make the comparison
                                        more strict. Defaults to 0.6.

        Returns:
            Tuple[Optional[str], Optional[str]]: The student number and name if a match is found,
                                                otherwise None, None.
        """
        try:
            query = f"SELECT student_id, full_name, face_encoding FROM {self._db_name}.students"
            self._cursor.execute(query)
        except pyodbc.Error as e:
            return {"status": "error", "message": f"Error occurred while attempting to fetch student's data from the database: {str(e)}", "code": 500}
        
        rows = self._cursor.fetchall()
        if not rows:
            return {"status": "error", "message": "No students found in the database.", "code": 404}
        
        for (student_number, student_name, face_encoding) in rows:
            face_encoding = pickle.loads(face_encoding)
            matches = fr.compare_faces([face_encoding], student_face_encoding, tolerance)

            if True in matches:
                return {"status": "success", "message": "Student successfully identified.", "code": 200, "student_number": student_number, "student_name": student_name}
        
        return {"status": "error", "message": "Student could not be identified.", "code": 404}
    
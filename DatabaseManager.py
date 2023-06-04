from __future__ import annotations
import pickle
import face_recognition as fr
import csv
import pyodbc
from typing import Tuple, Optional
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
        """
        config = configparser.ConfigParser()
        config.read('config.ini')
        self._db_name = config['DATABASE']['db_name']
        self._connection = self._create_connection()
        try:
            self._cursor = self._connection.cursor()
        except pyodbc.Error as e:
            print("Error creating cursor", e)
            self._cursor = None
    
    def _create_connection(self) -> Optional[pyodbc.Connection]:
        """
        Establishes a connection to the MySQL database using a specified configuration.

        Returns:
            Connection to the MySQL database or None if a connection could not be established.

        Raises:
            pyodbc.Error: If a connection to the database cannot be established.
        """
        config = configparser.ConfigParser()
        config.read('config.ini')

        username = config['DATABASE']['username']
        password = config['DATABASE']['password']
        driver = config['DATABASE']['driver']
        hostname = config['DATABASE']['host']
        try:
            connection_string = f"DRIVER={{{driver}}};SERVER={hostname};DATABASE={self._db_name};UID={username};PWD={password}"
            return pyodbc.connect(connection_string)
        except pyodbc.Error as e:
            print("Error connecting to the database", e)
            return None
    
    def close_connection(self) -> None:
        """
        Closes the cursor and connection to the database.

        Raises:
            pyodbc.Error: If the cursor/connection is already closed.
        """
        try:
            self._connection.execute("SELECT 1")
        except pyodbc.Error:
            print("Connection already closed.")
        else:
            self._connection.close()
    
    def __enter__(self) -> DatabaseManager:
        """
        Re-establishes the database connection and returns the DatabaseManager instance.
        This method is automatically called when the 'with' statement is used.

        Returns:
            self: The current instance of DatabaseManager.
        """
        config = configparser.ConfigParser()
        config.read('config.ini')
        self._db_name = config['DATABASE']['db_name']
        self._connection = self._create_connection()
        if self._connection:
            self._cursor = self._connection.cursor()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Closes the connection to the database. This method is automatically called 
        when exiting the 'with' statement, even if an error was raised within the 'with' block.

        Parameters:
            exc_type: The type of the exception that caused the context to be exited, if any.
            exc_value: The instance of the exception that caused the context to be exited, if any.
            traceback: A traceback object encapsulating the call stack at the point 
                    where the exception originally occurred, if any.
        """
        self.close_connection()

    def initialize_database(self) -> bool:
        """
        Initializes the specified database, removing all existing student data
        and repopulates it using the data from the student_info.csv file. 

        Returns:
            bool: True if the database was successfully initialized, False otherwise.
        """
        # Resetting (emptying) the database. 
        try :
            self._cursor.execute(f"DELETE FROM {self._db_name}.students")  
        except pyodbc.Error as e:
            print(f"Error occurred while attempting to delete from the database: {e}")
            return False

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
                        print(f"Image {img_path} not found.")
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
                            print(f"Error occurred while attempting to insert {student_number} into the database: {e}")
                            continue
        except FileNotFoundError:
            print("CSV file not found.")
            return False
        except Exception as e:
            print(f"Something went wrong: {e}")
            return False
        
        self._connection.commit()
        return True
    
    def add_student(self, student_number: str, student_name: str, img_path: str) -> bool:
        """
        Adds the specified student's information into the given database.

        Parameters:
            student_number (str): The ID number of the student.
            student_name (str): The name of the student.
            img_path (str): Path to the image of the student.

        Returns:
            bool: True if the student was successfully added, False otherwise.
        """
        try:
            img = fr.load_image_file("./images/" + img_path)
        except FileNotFoundError:
            print(f"{img_path} not found for student {student_name}.")
            return False
        
        face_encodings = fr.face_encodings(img)

        if len(face_encodings) == 0:
            print(f"No face encoding found for student {student_number}.")
            return False
        face_encoding = face_encodings[0]

        if len(face_encoding) > 0:
            serial_face_encoding = pickle.dumps(face_encoding)      
            query = f"INSERT INTO {self._db_name}.students (student_id, full_name, face_encoding) VALUES (?, ?, ?)"
            try:
                self._cursor.execute(query, (student_number, student_name, serial_face_encoding))
            except pyodbc.Error as e:
                print(f"Error occurred while attempting to insert {student_number} into the database: {e}")
                return False
        
        self._connection.commit()
        return True
    
    def identify_student(self, student_face_encoding: ndarray, tolerance: float = 0.6) -> Tuple[Optional[str], Optional[str]]:
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
            print(f"Error occurred while attempting to fetch student's data from the database: {e}")
            return None, None
        
        rows = self._cursor.fetchall()
        if not rows:
            print("No students found in the database.")
            return None, None
        
        for (student_number, student_name, face_encoding) in rows:
            face_encoding = pickle.loads(face_encoding)
            matches = fr.compare_faces([face_encoding], student_face_encoding, tolerance)

            if True in matches:
                return student_number, student_name
        
        print("Student could not be identified.")
        return None, None
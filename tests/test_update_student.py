import os, sys
import unittest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TestConfig
from app import app, SessionLocal, engine
from Models import Teacher, Base, User, Student, Parent
from unittest.mock import patch


class TestStudentUpdate(unittest.TestCase):
    def setUp(self):
        os.environ["FLASK_ENV"] = "testing"
        app.config.from_object(TestConfig)  # Use test configuration
        self.client = app.test_client()
        Base.metadata.create_all(bind=engine)  # Create all tables
        self.session = SessionLocal()  # Now this should connect to your SQLite database

        # Create a student and add it to the database
        self.student = Student(name="Student1", email="student1@gmail.com", password="password")
        self.student2 = Student(name="Student2", email="student2@gmail.com", password="password")
        self.session.add(self.student)
        self.session.add(self.student2)
        self.session.commit()

    def tearDown(self):
        self.session.query(Teacher).delete()
        self.session.query(Student).delete()
        self.session.query(Parent).delete()
        self.session.query(User).delete()
        self.session.commit()
        # Close the session
        self.session.close()
        Base.metadata.drop_all(bind=engine)

    @patch('flask_login.utils._get_user')
    def test_missing_fields(self, get_user):
        get_user.return_value = self.student
        response = self.client.put('/students', data={}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "No fields to update were provided")

    @patch('flask_login.utils._get_user')
    def test_update_name(self, get_user):
        get_user.return_value = self.student
        response = self.client.put('/students', data={"name": "NewStudent"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Student updated")

    @patch('flask_login.utils._get_user')
    def test_update_email(self, get_user):
        get_user.return_value = self.student
        response = self.client.put('/students', data={"email": "newstudent@gmail.com"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Student updated")
    
    @patch('flask_login.utils._get_user')
    def test_update_image(self, get_user):
        get_user.return_value = self.student
        with open('./images/cristiano.jpg', 'rb') as img:
            response = self.client.put('/students', data={"image": img}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Student updated")
    
    @patch('flask_login.utils._get_user')
    def test_update_image_noface(self, get_user):
        get_user.return_value = self.student
        with open('./images/white.png', 'rb') as img:
            response = self.client.put('/students', data={"image": img}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 422)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "Cannot recognize a face from the image")
    
    @patch('flask_login.utils._get_user')
    def test_update_all(self, get_user):
        get_user.return_value = self.student
        with open('./images/pewdiepie.jpg', 'rb') as img:
            response = self.client.put('/students', data={"name": "NewStudent1", "email": "newstudent1@gmail.com", "image": img}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Student updated")

    @patch('flask_login.utils._get_user')
    def test_email_already_exists(self, get_user):
        get_user.return_value = self.student
        response = self.client.put('/students', data={"email": "student2@gmail.com"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "A user with this email already exists")
    
    @patch('flask_login.utils._get_user')
    def test_invalid_email_format(self, get_user):
        get_user.return_value = self.student
        response = self.client.put('/students', data={"email": "student"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid email format')
    
    @patch('flask_login.utils._get_user')
    def test_invalid_email_length(self, get_user):
        get_user.return_value = self.student
        response = self.client.put('/students', data={"email": "t" * 246 + "@gmail.com"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid email format')
    
    @patch('flask_login.utils._get_user')
    def test_invalid_name_length(self, get_user):
        get_user.return_value = self.student
        response = self.client.put('/students', data={"name": "a" * 61}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Name too long')


if __name__ == "__main__":
    unittest.main()

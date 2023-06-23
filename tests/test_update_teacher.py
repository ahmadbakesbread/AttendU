import os, sys
import unittest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TestConfig
from app import app, SessionLocal, engine
from Models import Teacher, Base, User, Student, Parent
from unittest.mock import patch


class TestTeacherUpdate(unittest.TestCase):
    def setUp(self):
        app.config.from_object(TestConfig)  # Use test configuration
        self.client = app.test_client()
        Base.metadata.create_all(bind=engine)  # Create all tables
        self.session = SessionLocal()  # Now this should connect to your SQLite database

        # Create a teacher and add it to the database
        self.teacher = Teacher(name="Teacher1", email="teacher1@gmail.com", password="password")
        self.teacher2 = Teacher(name="Teacher2", email="teacher2@gmail.com", password="password")
        self.session.add(self.teacher)
        self.session.add(self.teacher2)
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
        get_user.return_value = self.teacher
        response = self.client.put('/teachers', data={}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "No fields to update were provided")

    @patch('flask_login.utils._get_user')
    def test_update_name(self, get_user):
        get_user.return_value = self.teacher
        response = self.client.put('/teachers', data={"name": "NewTeacher"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Teacher updated")

    @patch('flask_login.utils._get_user')
    def test_update_email(self, get_user):
        get_user.return_value = self.teacher
        response = self.client.put('/teachers', data={"email": "newteacher@gmail.com"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Teacher updated")
    
    @patch('flask_login.utils._get_user')
    def test_update_image(self, get_user):
        get_user.return_value = self.teacher
        with open('./images/cristiano.jpg', 'rb') as img:
            response = self.client.put('/teachers', data={"image": img}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Teacher updated")
    
    @patch('flask_login.utils._get_user')
    def test_update_all(self, get_user):
        get_user.return_value = self.teacher
        with open('./images/pewdiepie.jpg', 'rb') as img:
            response = self.client.put('/teachers', data={"name": "NewTeacher1", "email": "newteacher1@gmail.com", "image": img}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Teacher updated")

    @patch('flask_login.utils._get_user')
    def test_email_already_exists(self, get_user):
        get_user.return_value = self.teacher
        response = self.client.put('/teachers', data={"email": "teacher2@gmail.com"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "A user with this email already exists")
    
    @patch('flask_login.utils._get_user')
    def test_invalid_email_format(self, get_user):
        get_user.return_value = self.teacher
        response = self.client.put('/teachers', data={"email": "teacher"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid email format')
    
    @patch('flask_login.utils._get_user')
    def test_invalid_email_length(self, get_user):
        get_user.return_value = self.teacher
        response = self.client.put('/teachers', data={"email": "t" * 246 + "@gmail.com"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid email format')
    
    @patch('flask_login.utils._get_user')
    def test_invalid_name_length(self, get_user):
        get_user.return_value = self.teacher
        response = self.client.put('/teachers', data={"name": "a" * 61}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Name too long')


if __name__ == "__main__":
    unittest.main()

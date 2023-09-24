import os, sys
import unittest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TestConfig
from app import app, SessionLocal, engine
from Models import Teacher, Base, User, Student, Parent, Class
from unittest.mock import patch


class TestCreateClass(unittest.TestCase):
    def setUp(self):
        app.config.from_object(TestConfig)  # Use test configuration
        self.client = app.test_client()
        Base.metadata.create_all(bind=engine)  # Create all tables
        self.session = SessionLocal()  # Now this should connect to your SQLite database

        # Create a teacher and add it to the database
        self.teacher = Teacher(name="Teacher1", email="teacher1@gmail.com", password="password")
        self.teacher2 = Teacher(name="Teacher2", email="teacher2@gmail.com", password="password")
        self.parent = Parent(name="Parent", email="parent@gmail.com", password="password")
        self.student = Student(name="Student", email="student@gmail.com", password="password")
        self.session.add(self.teacher)
        self.session.add(self.teacher2)
        self.session.add(self.parent)
        self.session.add(self.student)
        self.session.commit()

    def tearDown(self):
        self.session.query(Teacher).delete()
        self.session.query(Student).delete()
        self.session.query(Parent).delete()
        self.session.query(User).delete()
        self.session.query(Class).delete()
        self.session.commit()
        # Close the session
        self.session.close()
        Base.metadata.drop_all(bind=engine)

    @patch('flask_login.utils._get_user')
    def test_create_class_as_parent(self, get_user):
        get_user.return_value = self.parent
        response = self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "User is not a teacher")

    @patch('flask_login.utils._get_user')
    def test_create_class_as_student(self, get_user):
        get_user.return_value = self.student
        response = self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "User is not a teacher")
    
    @patch('flask_login.utils._get_user')
    def test_missing_class_name(self, get_user):
        get_user.return_value = self.teacher
        response = self.client.post('/classes', data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "Missing class name")
    
    @patch('flask_login.utils._get_user')
    def test_invalid_class_name(self, get_user):
        get_user.return_value = self.teacher
        response = self.client.post('/classes', data=json.dumps({"class_name": "c" * 61}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "Class name too long")
    
    @patch('flask_login.utils._get_user')
    def test_create_class_successful(self, get_user):
        get_user.return_value = self.teacher
        response = self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Class created")
    
    @patch('flask_login.utils._get_user')
    def test_repeated_class_name(self, get_user):
        get_user.return_value = self.teacher
        self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        response = self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "A class with this name already exists for this teacher")

if __name__ == "__main__":
    unittest.main()

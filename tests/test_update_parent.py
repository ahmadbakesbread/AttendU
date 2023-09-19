import os, sys
import unittest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TestConfig
from app import app, SessionLocal, engine
from Models import Teacher, Base, User, Student, Parent
from unittest.mock import patch


class TestParentUpdate(unittest.TestCase):
    def setUp(self):
        os.environ["FLASK_ENV"] = "testing"
        app.config.from_object(TestConfig)  # Use test configuration
        self.client = app.test_client()
        Base.metadata.create_all(bind=engine)  # Create all tables
        self.session = SessionLocal()  # Now this should connect to your SQLite database

        # Create a parent and add it to the database
        self.parent = Parent(name="Parent1", email="parent1@gmail.com", password="password")
        self.parent2 = Parent(name="Parent2", email="parent2@gmail.com", password="password")
        self.session.add(self.parent)
        self.session.add(self.parent2)
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
        get_user.return_value = self.parent
        response = self.client.put('/parents', data={}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "No fields to update were provided")

    @patch('flask_login.utils._get_user')
    def test_update_name(self, get_user):
        get_user.return_value = self.parent
        response = self.client.put('/parents', data={"name": "NewParent"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Parent updated")

    @patch('flask_login.utils._get_user')
    def test_update_email(self, get_user):
        get_user.return_value = self.parent
        response = self.client.put('/parents', data={"email": "newparent@gmail.com"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Parent updated")
    
    @patch('flask_login.utils._get_user')
    def test_update_image(self, get_user):
        get_user.return_value = self.parent
        with open('./images/cristiano.jpg', 'rb') as img:
            response = self.client.put('/parents', data={"image": img}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Parent updated")
    
    @patch('flask_login.utils._get_user')
    def test_update_all(self, get_user):
        get_user.return_value = self.parent
        with open('./images/pewdiepie.jpg', 'rb') as img:
            response = self.client.put('/parents', data={"name": "NewParent1", "email": "newparent1@gmail.com", "image": img}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Parent updated")

    @patch('flask_login.utils._get_user')
    def test_email_already_exists(self, get_user):
        get_user.return_value = self.parent
        response = self.client.put('/parents', data={"email": "parent2@gmail.com"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "A user with this email already exists")
    
    @patch('flask_login.utils._get_user')
    def test_invalid_email_format(self, get_user):
        get_user.return_value = self.parent
        response = self.client.put('/parents', data={"email": "parent"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid email format')
    
    @patch('flask_login.utils._get_user')
    def test_invalid_email_length(self, get_user):
        get_user.return_value = self.parent
        response = self.client.put('/parents', data={"email": "t" * 246 + "@gmail.com"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid email format')
    
    @patch('flask_login.utils._get_user')
    def test_invalid_name_length(self, get_user):
        get_user.return_value = self.parent
        response = self.client.put('/parents', data={"name": "a" * 61}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Name too long')


if __name__ == "__main__":
    unittest.main()

import os, sys
import unittest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TestConfig
from app import app, SessionLocal, engine
from Models import Teacher, Base, User, Student, Parent


class TestTeacherRegistration(unittest.TestCase):
    def setUp(self):
        os.environ["FLASK_ENV"] = "testing"
        app.config.from_object(TestConfig)  # Use test configuration
        self.client = app.test_client()
        Base.metadata.create_all(bind=engine)  # Create all tables
        self.session = SessionLocal()

    def tearDown(self):
        # Delete all types of objects that were created in the tests.
        self.session.query(Teacher).delete()
        self.session.query(Student).delete()
        self.session.query(Parent).delete()
        self.session.query(User).delete()
        # More delete queries for other types of objects...
        self.session.commit()  # Ensure session is committed
        self.session.close()
        Base.metadata.drop_all(bind=engine)

    def test_name_missing(self):
        response = self.client.post('/teachers', data={"email": "teacher@gmail.com", "password": "password"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Missing required fields')

    def test_email_missing(self):
        response = self.client.post('/teachers', data={"name": "Example", "password": "password"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Missing required fields')
    
    def test_password_missing(self):
        response = self.client.post('/teachers', data={"email": "teacher@gmail.com", "name": "Example"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Missing required fields')
    
    def test_long_name(self):
        response = self.client.post('/teachers', data={"name": "a" * 61, "email": "teacher@gmail.com", "password": "password"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Name too long')
    
    def test_invalid_email_format(self):
        response = self.client.post('/teachers', data={"name": "Example", "email": "teacher", "password": "password"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid email format')
    
    def test_invalid_email_length(self):
        response = self.client.post('/teachers', data={"name": "Example", "email": "t" * 246 + "@gmail.com", "password": "password"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid email format')
    
    def test_user_email_exists(self):
        self.client.post('/teachers', data={"name": "Example", "email": "teacher@gmail.com", "password": "password"}, content_type='multipart/form-data')
        response = self.client.post('/teachers', data={"name": "Example2", "email": "teacher@gmail.com", "password": "password"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'A user with this email already exists')
    
    def test_user_image_missing(self):
        response = self.client.post('/teachers', data={"name": "Example", "email": "teacher@gmail.com", "password": "password"}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Teacher created')
    
    def test_user_with_image(self):
        with open('./images/cristiano.jpg', 'rb') as img:
            response = self.client.post('/teachers',
                                        content_type='multipart/form-data',
                                        data={"name": "Example", "email": "teacher@gmail.com", "password": "password", "image": img},
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Teacher created')


if __name__ == "__main__":
    unittest.main()

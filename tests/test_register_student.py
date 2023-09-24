import os, sys
import unittest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TestConfig
from app import app, SessionLocal, engine
from Models import Teacher, Base, User, Student, Parent


class TestStudentRegistration(unittest.TestCase):
    def setUp(self):
        os.environ["FLASK_ENV"] = "testing"
        app.config.from_object(TestConfig)  # Use test configuration
        self.client = app.test_client()
        Base.metadata.create_all(bind=engine)  # Create all tables
        self.session = SessionLocal()  # Now this should connect to your SQLite database

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
        with open('./images/cristiano.jpg', 'rb') as img:
            response = self.client.post('/students',
                                        content_type='multipart/form-data',
                                        data={"email": "student@gmail.com", "password": "password", "image": img},
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Missing required fields')

    def test_email_missing(self):
        with open('./images/cristiano.jpg', 'rb') as img:
            response = self.client.post('/students',
                                        content_type='multipart/form-data',
                                        data={"name": "Example", "password": "password", "image": img},
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Missing required fields')
    
    def test_password_missing(self):
        with open('./images/cristiano.jpg', 'rb') as img:
            response = self.client.post('/students',
                                        content_type='multipart/form-data',
                                        data={"name": "Example", "email": "student@gmail.com", "image": img},
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Missing required fields')
    
    def test_long_name(self):
        with open('./images/cristiano.jpg', 'rb') as img:
            response = self.client.post('/students',
                                        content_type='multipart/form-data',
                                        data={"name": "a" * 61, "email": "student@gmail.com", "password": "password", "image": img},
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Name too long')
    
    def test_invalid_email_format(self):
        with open('./images/cristiano.jpg', 'rb') as img:
            response = self.client.post('/students',
                                        content_type='multipart/form-data',
                                        data={"name": "Example", "email": "students", "password": "password", "image": img},
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid email format')
    
    def test_invalid_email_length(self):
        with open('./images/cristiano.jpg', 'rb') as img:
            response = self.client.post('/students',
                                        content_type='multipart/form-data',
                                        data={"name": "Example", "email": "t" * 246 + "@gmail.com", "password": "password", "image": img},
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid email format')
    
    def test_user_email_exists(self):
        with open('./images/cristiano.jpg', 'rb') as img:
            self.client.post('/students',
                            content_type='multipart/form-data',
                            data={"name": "Example", "email": "student@gmail.com", "password": "password", "image": img},
                            follow_redirects=True)
        with open('./images/lebron.jpg', 'rb') as img:
            response = self.client.post('/students',
                                        content_type='multipart/form-data',
                                        data={"name": "Example", "email": "student@gmail.com", "password": "password", "image": img},
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'A user with this email already exists')
    
    def test_user_image_missing(self):
        response = self.client.post('/students', content_type='multipart/form-data', data={"name": "Example", "email": "student@gmail.com", "password": "password"})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Missing required fields')

    def test_user_with_empty_image(self):
        with open('./images/white.png', 'rb') as img:
            response = self.client.post('/students',
                                        content_type='multipart/form-data',
                                        data={"name": "Example", "email": "student@gmail.com", "password": "password", "image": img},
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 422)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Cannot recognize a face from the image')
    
    def test_user_with_image(self):
        with open('./images/cristiano.jpg', 'rb') as img:
            response = self.client.post('/students',
                                        content_type='multipart/form-data',
                                        data={"name": "Example", "email": "student@gmail.com", "password": "password", "image": img},
                                        follow_redirects=True)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Student created')


if __name__ == "__main__":
    unittest.main()
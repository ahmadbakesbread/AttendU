import unittest
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TestConfig
import json
from app import app, SessionLocal, engine
from flask import session
from flask_login import current_user
from Models import Teacher, User, Base

class LoginTestCase(unittest.TestCase):
    def setUp(self):
        app.config.from_object(TestConfig)  # Use test configuration
        app.config['WTF_CSRF_ENABLED'] = False
        Base.metadata.create_all(bind=engine)  # Create all tables
        self.client = app.test_client()
        self.session = SessionLocal()  # Now this should connect to your SQLite database
        self.client.post('/teachers', data={"name": "Teacher", "email": "teacher@gmail.com", "password": "password"}, content_type='multipart/form-data')
        self.session.commit()
    
    def tearDown(self) -> None:
        self.session.query(Teacher).delete()
        self.session.query(User).delete()
        self.session.commit()
        self.session.close()
        Base.metadata.drop_all(bind=engine)
    
    def test_login_email_does_not_exist(self):
        with self.client as c:
            response = c.post('/login', json=dict(
                email="teacher2@gmail.com",
                password="password"
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(current_user.is_authenticated)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 'error')
            self.assertEqual(data['message'], "Email could not be found")
    
    def test_login_invalid_email(self):
        with self.client as c:
            response = c.post('/login', json=dict(
                email="teacher",
                password="password"
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 400)
            self.assertFalse(current_user.is_authenticated)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 'error')
            self.assertEqual(data['message'], "Invalid email format")
    
    def test_login_incorrect_password(self):
        with self.client as c:
            response = c.post('/login', json=dict(
                email="teacher@gmail.com",
                password="incorrectpassword"
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(current_user.is_authenticated)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 'error')
            self.assertEqual(data['message'], "Incorrect password")
    
    def test_login_deleted_user(self):
        # Login
        with self.client as c:
            response = c.post('/login', json=dict(
                email="teacher@gmail.com",
                password="password"
            ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        self.client.delete('/users', content_type='application/json')

        with self.client as c:
            response = c.post('/login', json=dict(
                email="teacher@gmail.com",
                password="password"
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(current_user.is_authenticated)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 'error')
            self.assertEqual(data['message'], "Email could not be found")

    def test_login_logout(self):
        with self.client as c:
            response = c.post('/login', json=dict(
                email="teacher@gmail.com",
                password="password"
            ), follow_redirects=True)
            self.assertTrue(current_user.is_authenticated)
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 200)

        # Test logout
        with self.client as c:
            response = c.get('/logout', follow_redirects=True)
            self.assertFalse(current_user.is_authenticated)
            self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
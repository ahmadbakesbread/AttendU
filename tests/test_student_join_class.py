import os, sys
import unittest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TestConfig
from app import app, SessionLocal, engine
from Models import Teacher, Base, User, Student, Parent, ConnectionRequest, Class
from unittest.mock import patch


class TestStudentJoinClass(unittest.TestCase):
    def setUp(self):
        os.environ["FLASK_ENV"] = "testing"
        app.config.from_object(TestConfig)  # Use test configuration
        self.client = app.test_client()
        Base.metadata.create_all(bind=engine)  # Create all tables
        self.session = SessionLocal() 

        # Create a parent and add it to the database
        self.student1 = Student(name="Student1", email="student1@gmail.com", password="password") # student created like this only for testing purposes.
        self.student2 = Student(name="Student2", email="student2@gmail.com", password="password")
        self.teacher1 = Teacher(name="Teacher1", email="teacher1@gmail.com", password="password")
        self.teacher2 = Teacher(name="Teacher2", email="teacher2@gmail.com", password="password")
        self.parent = Parent(name="Parent", email="parent@gmail.com", password="password")
        self.session.add(self.student1)
        self.session.add(self.student2)
        self.session.add(self.teacher1)
        self.session.add(self.teacher2)
        self.session.commit()

    def tearDown(self):
        self.session.query(Teacher).delete()
        self.session.query(Student).delete()
        self.session.query(Parent).delete()
        self.session.query(User).delete()
        self.session.query(Class).delete()
        self.session.query(ConnectionRequest).delete()
        self.session.commit()
        # Close the session
        self.session.close()
        Base.metadata.drop_all(bind=engine)

    @patch('flask_login.utils._get_user')
    def test_request_join_class_as_student(self, get_user):
        # Login as Teacher
        get_user.return_value = self.teacher1
        self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        created_class = self.session.query(Class).filter_by(teacher_id=self.teacher1.id).first()
        self.assertIsNotNone(created_class)
        response = self.client.get(f'classes/{created_class.id}', content_type='application/json')
        class_code = json.loads(response.data)['data']
        # Login as Student
        get_user.return_value = self.student1
        response = self.client.post('/students/classes/join', data=json.dumps({"code": class_code}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Join request sent successfully")

    
    @patch('flask_login.utils._get_user')
    def test_request_join_existing_request(self, get_user):
        # Login as Teacher
        get_user.return_value = self.teacher1
        self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        created_class = self.session.query(Class).filter_by(teacher_id=self.teacher1.id).first()
        self.assertIsNotNone(created_class)
        response = self.client.get(f'classes/{created_class.id}', content_type='application/json')
        class_code = json.loads(response.data)['data']
        # Login as Student
        get_user.return_value = self.student1
        self.client.post('/students/classes/join', data=json.dumps({"code": class_code}), content_type='application/json')
        response = self.client.post('/students/classes/join', data=json.dumps({"code": class_code}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "Request is already pending")
    
    @patch('flask_login.utils._get_user')
    def test_request_join_class_existing_request2(self, get_user):
        # Login as Teacher
        get_user.return_value = self.teacher1
        self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        created_class = self.session.query(Class).filter_by(teacher_id=self.teacher1.id).first()
        self.assertIsNotNone(created_class)
        response = self.client.get(f'classes/{created_class.id}', content_type='application/json')
        class_code = json.loads(response.data)['data']
        # Login as Student
        get_user.return_value = self.student1
        self.client.post('/students/classes/join', data=json.dumps({"code": class_code}), content_type='application/json')
        # Login as Teacher
        get_user.return_value = self.teacher1
        response = self.client.post(f'/teacher/classes/{created_class.id}/send', data=json.dumps({"email": "student1@gmail.com"}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], "Request accepted")
    
    @patch('flask_login.utils._get_user')
    def test_join_class_as_parent(self, get_user):
        # Login as Teacher
        get_user.return_value = self.teacher1
        self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        created_class = self.session.query(Class).filter_by(teacher_id=self.teacher1.id).first()
        self.assertIsNotNone(created_class)
        response = self.client.get(f'classes/{created_class.id}', content_type='application/json')
        class_code = json.loads(response.data)['data']
        # Login as Parent
        get_user.return_value = self.parent
        response = self.client.post('/students/classes/join', data=json.dumps({"code": class_code}), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "Not authorized")
    
    @patch('flask_login.utils._get_user')
    def test_join_class_as_teacher(self, get_user):
        # Login as Teacher
        get_user.return_value = self.teacher1
        self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        created_class = self.session.query(Class).filter_by(teacher_id=self.teacher1.id).first()
        self.assertIsNotNone(created_class)
        response = self.client.get(f'classes/{created_class.id}', content_type='application/json')
        class_code = json.loads(response.data)['data']
        response = self.client.post('/students/classes/join', data=json.dumps({"code": class_code}), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "Not authorized")
    
    @patch('flask_login.utils._get_user')
    def test_request_join_class_invalid_code(self, get_user):
        # Login as Teacher
        get_user.return_value = self.teacher1
        self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        # Login as Student
        get_user.return_value = self.student1
        response = self.client.post('/students/classes/join', data=json.dumps({"code": "A"}), content_type='application/json')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "Class not found")
    
    @patch('flask_login.utils._get_user')
    def test_request_join_class_missing_code(self, get_user):
        # Login as Teacher
        get_user.return_value = self.teacher1
        self.client.post('/classes', data=json.dumps({"class_name": "class"}), content_type='application/json')
        # Login as Student
        get_user.return_value = self.student1
        response = self.client.post('/students/classes/join', data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], "No class code provided")


if __name__ == "__main__":
    unittest.main()
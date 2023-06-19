from flask import Flask, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from Models import Base, Teacher, Class, User, Student, Parent
from configparser import ConfigParser
from urllib.parse import quote
from Helpers import is_valid_email
import bcrypt

app = Flask(__name__)

config = ConfigParser()
config.read('config.ini')

host = config['DATABASE']['host']
user = config['DATABASE']['username']
password = config['DATABASE']['password']
database = config['DATABASE']['db_name']
driver = config['DATABASE']['driver']
port = config['DATABASE']['port']

password = quote(password, safe='')

# Create the SQLAlchemy engine
engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
# Use this to create all the tables and information. 
# Only need to run this once!

### User Endpoints ###

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()
    session.close()
    
    if user is None or not bcrypt.checkpw(password.encode('utf-8'), user.password.decode('utf-8')):
        return jsonify({"status": "error", "message": "Incorrect email or password", "code": 403}), 403

    # Log the user in
    login_user(user)

    return jsonify({"status": "success", "message": "Login successful", "code": 200}), 200

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"status": "success", "message": "Logged out", "code": 200}), 200

@app.route('/users', methods=['DELETE'])
@login_required
def delete_user():
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=current_user.id).first()
        
        if not user:
            return jsonify({"status": "error", "message": "User not found", "code": 404}), 404
        
        session.delete(user)
        session.commit()
        return jsonify({"status": "success", "message": "User successfully deleted", "code": 200}), 200
    
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while deleting the user", "code": 500}), 500
    
    finally:
        session.close()

### Teacher Endpoints ###

@app.route('/teachers', methods=['POST'])
def register_teacher():
    session = SessionLocal()
    data = request.json

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    image = data.get('image')
    
    try:
        if not name or not email or not password:
            return jsonify({"status": "error", "message": "Missing required fields", "code": 400}), 400

        # Check if a teacher with this email already exists
        existing_teacher = session.query(Teacher).filter_by(email=email).first()
        
        if existing_teacher:
            return jsonify({"status": "error", "message": "A teacher with this email already exists", "code": 400}), 400

        # Hash password before saving
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user = User(email=email, password=hashed_password)
        session.add(user)
        session.flush()
        
        new_teacher = Teacher(user_id=user.id, name=name, image=image)

        session.add(new_teacher)
        session.commit()
        return jsonify({"status": "success", "message": "Teacher created", "code": 201}), 201

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while creating the teacher", "code": 500}), 500

    finally:
        session.close()

@app.route('/teachers', methods=['PUT'])
@login_required
def update_teacher():
    session = SessionLocal()
    data = request.json

    name = data.get('name')
    email = data.get('email')
    image = data.get('image')

    try:
        # If no fields to update were provided
        if not name and not email and not image:
            return jsonify({"status": "error", "message": "No fields to update were provided", "code": 400}), 400

        # Find the teacher
        teacher = session.query(Teacher).filter_by(user_id=current_user.id).first()
        if not teacher:
            return jsonify({"status": "error", "message": "Teacher not found", "code": 404}), 404

        # If an email was provided, validate it
        if email and not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email Format", "code": 400}), 400
        
        # Update the teacher's profile
        teacher.update_profile(session=session, name=name, email=email, image=image)
        return jsonify({"status": "success", "message": "Teacher updated", "code": 200}), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while updating the teacher", "code": 500}), 500

    finally:
        session.close()

@app.route('/classes', methods=['POST'])
@login_required  # Only logged in users can create a class
def create_class():
    session = SessionLocal()

    try:
        data = request.json
        class_name = data.get('class_name')
        
        if not class_name:
            return jsonify({"status": "error", "message": "Missing class name", "code": 400})
        
        if len(class_name) > 60:
            return jsonify({"status": "error", "message": "Class name too long", "code": 400})

        # Check if a class with this name already exists for this teacher
        existing_class = session.query(Class).filter_by(class_name=class_name, teacher_id=teacher.id).first()
        if existing_class:
            return jsonify({"status": "error", "message": "A class with this name already exists for this teacher", "code": 400})

        # Check if the teacher exists
        teacher = session.query(Teacher).filter_by(user_id=current_user.id).first()
        if not teacher:
            return jsonify({"status": "error", "message": "Teacher not found", "code": 404})

        new_class = Class(teacher_id=teacher.id, class_name=class_name)

        session.add(new_class)
        session.commit()
        return jsonify({"status": "success", "message": "Class created", "code": 201}), 201

    except SQLAlchemyError:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while creating the class", "code": 500}), 500

    finally:
        session.close()

@app.route('/classes/<int:class_id>', methods=['DELETE'])
@login_required
def delete_class(class_id):
    session = SessionLocal()
    try:
        # Find the class with the given id
        class_ = session.query(Class).filter_by(id=class_id).first()

        # If the class doesn't exist
        if not class_:
            return jsonify({"status": "error", "message": "Class not found", "code": 404}), 404

        # If the logged in user is not the teacher of this class
        if class_.teacher_id != current_user.id:
            return jsonify({"status": "error", "message": "You are not the teacher of this class", "code": 403}), 403

        # Delete the class
        session.delete(class_)
        session.commit()
        return jsonify({"status": "success", "message": "Class successfully deleted", "code": 200}), 200
    
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while deleting the class", "code": 500}), 500
    
    finally:
        session.close()

@app.route('/classes/<int:class_id>/students/<int:student_id>', methods=['PUT'])
@login_required
def add_student_to_class(class_id, student_id):
    session = SessionLocal()
    
    try:
        # Check if the logged in user is the teacher of the class
        teacher_class = session.query(Class).filter_by(id=class_id, teacher_id=current_user.get_id()).first()
        if not teacher_class:
            return jsonify({"status": "error", "message": "Unauthorized", "code": 403}), 403

        student = session.query(Student).filter_by(id=student_id).first()
        if not student:
            return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404

        # Add student to class
        teacher_class.students.append(student)
        session.commit()
        return jsonify({"status": "success", "message": "Student successfully added to the class", "code": 200}), 200
    
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while adding the student to the class", "code": 500}), 500
    
    finally:
        session.close()


### Parent Endpoints ###

### Student Endpoints ###

if __name__ == '__main__':
    app.run(debug=True)

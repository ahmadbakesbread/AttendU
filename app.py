from flask import Flask, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from Models import Base, Teacher, Class, User, Student, Parent, ConnectionRequest
from configparser import ConfigParser
from urllib.parse import quote
from Helpers import is_valid_email
import bcrypt

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

config = ConfigParser()
config.read('config.ini')

app.config['SECRET_KEY'] = config['FLASK']['secret_key']

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

@login_manager.user_loader
def load_user(user_id):
    session = SessionLocal()
    return session.query(User).get(int(user_id))

### User Endpoints ###

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()
    session.close()

    if not is_valid_email(email):
        return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400 
    
    if user is None:
        return jsonify({"status": "error", "message": "Email does not exist", "code": 403}), 403
    
    if not bcrypt.checkpw(password.encode('utf-8'), user.password):
        return jsonify({"status": "error", "message": "Incorrect password", "code": 403}), 403

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

@app.route('/users/requests/send', methods=['POST'])
@login_required
def send_request():
    recipient_email = request.json.get('email')

    session = SessionLocal()
    try:
        recipient = session.query(User).filter_by(email=recipient_email).first()
        if not recipient:
            return jsonify({"status": "error", "message": "User not found", "code": 404}), 404

        existing_request = session.query(ConnectionRequest).filter_by(sender_id=current_user.id, recipient_email=recipient_email).first()
        if existing_request and existing_request.status == 'pending':
            return jsonify({"status": "error", "message": "Request is already pending", "code": 400}), 400

        new_request = ConnectionRequest(sender_id=current_user.id, recipient_email=recipient_email)
        session.add(new_request)
        session.commit()

        return jsonify({"status": "success", "message": "Request sent successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": str(e), "code": 500}), 500

    finally:
        session.close()

@app.route('/users/requests/<int:request_id>/respond', methods=['POST'])
@login_required
def respond_to_request(request_id):
    response = request.json.get('response')

    session = SessionLocal()
    try:
        connection_request = session.query(ConnectionRequest).filter_by(id=request_id, recipient_email=current_user.email).first()
        if not connection_request:
            return jsonify({"status": "error", "message": "Request not found", "code": 404}), 404

        if response == 'accept':
            if isinstance(current_user._get_current_object(), Parent):
                connection_request.sender.parents.append(current_user._get_current_object())
            else:
                connection_request.sender.children.append(current_user._get_current_object())

            session.delete(connection_request)
            session.commit()
            return jsonify({"status": "success", "message": "Request accepted", "code": 200}), 200

        elif response == 'reject':
            session.delete(connection_request)
            session.commit()
            return jsonify({"status": "success", "message": "Request rejected", "code": 200}), 200

        else:
            return jsonify({"status": "error", "message": "Invalid response", "code": 400}), 400

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": str(e), "code": 500}), 500

    finally:
        session.close()

@app.route('/users/connections/<int:user_id>/delete', methods=['DELETE'])
@login_required
def delete_connection(user_id):
    session = SessionLocal()
    try:
        user_to_remove = session.query(User).filter_by(id=user_id).first()
        if not user_to_remove:
            return jsonify({"status": "error", "message": "User not found", "code": 404}), 404

        if isinstance(current_user._get_current_object(), Parent) and user_to_remove in current_user.children:
            current_user.children.remove(user_to_remove)
        elif isinstance(current_user._get_current_object(), Student) and user_to_remove in current_user.parents:
            current_user.parents.remove(user_to_remove)
        else:
            return jsonify({"status": "error", "message": "No connection found", "code": 404}), 404

        session.commit()
        return jsonify({"status": "success", "message": "Connection deleted", "code": 200}), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": str(e), "code": 500}), 500

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
        
        if len(name) > 60:
            return jsonify({"status": "error", "message": "Name too long", "code": 400}), 400
        
        if not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

        # Check if a teacher with this email already exists
        existing_user = session.query(User).filter_by(email=email).first()
        
        if existing_user:
            return jsonify({"status": "error", "message": "A user with this email already exists", "code": 400}), 400

        # Hash password before saving        
        new_teacher = Teacher(name=name, email=email, password=password, image=image)

        session.add(new_teacher)
        session.commit()
        return jsonify({"status": "success", "message": "Teacher created", "code": 201}), 201

    except SQLAlchemyError as e:
        session.rollback()
        print(str(e))
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
        
        if not isinstance(current_user, Teacher):
            return jsonify({"status": "error", "message": "User is not a teacher", "code": 403}), 403

        # Find the teacher
        teacher = session.query(Teacher).filter_by(id=current_user.id).first()
        if not teacher:
            return jsonify({"status": "error", "message": "Teacher not found", "code": 404}), 404

        # If an email was provided, validate it
        if email and not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email Format", "code": 400}), 400
        
        if session.query(User).filter_by(email=email).first():
            return jsonify({"status": "error", "message": "A user with this email already exists", "code": 403}), 403
        
        # Update the teacher's profile
        teacher.update_profile(session=session, name=name, email=email, image=image)
        return jsonify({"status": "success", "message": "Teacher updated", "code": 200}), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while updating the teacher", "code": 500}), 500

    finally:
        session.close()

### Class/Teacher Endpoints ###
@app.route('/classes', methods=['POST'])
@login_required
def create_class():
    session = SessionLocal()

    try:
        data = request.json
        class_name = data.get('class_name')

        # Check if user is a teacher
        if not isinstance(current_user, Teacher):
            return jsonify({"status": "error", "message": "User is not a teacher", "code": 404}), 403

        # Check if the teacher exists
        teacher = session.query(Teacher).filter_by(id=current_user.id).first()
        if not teacher:
            return jsonify({"status": "error", "message": "Teacher not found", "code": 404}), 404
        
        if not class_name:
            return jsonify({"status": "error", "message": "Missing class name", "code": 400}), 400
        
        if len(class_name) > 60:
            return jsonify({"status": "error", "message": "Class name too long", "code": 400}), 400

        # Check if a class with this name already exists for this teacher
        existing_class = session.query(Class).filter_by(class_name=class_name, teacher_id=teacher.id).first()
        if existing_class:
            return jsonify({"status": "error", "message": "A class with this name already exists for this teacher", "code": 400}), 400

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

### Parent Endpoints ###

@app.route('/parents', methods=['POST'])
def register_parent():
    session = SessionLocal()
    data = request.json

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    image = data.get('image')
    
    try:
        if not name or not email or not password:
            return jsonify({"status": "error", "message": "Missing required fields", "code": 400}), 400
        
        if len(name) > 60:
            return jsonify({"status": "error", "message": "Name too long", "code": 400}), 400
        
        if not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

        # Check if a parent with this email already exists
        existing_user = session.query(User).filter_by(email=email).first()
        
        if existing_user:
            return jsonify({"status": "error", "message": "A user with this email already exists", "code": 400}), 400

        new_parent = Parent(name=name, email=email, password=password, image=image)

        session.add(new_parent)
        session.commit()
        return jsonify({"status": "success", "message": "Parent created", "code": 201}), 201

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while creating the parent", "code": 500}), 500

    finally:
        session.close()

@app.route('/parents', methods=['PUT'])
def update_parent():
    session = SessionLocal()
    data = request.json

    name = data.get('name')
    email = data.get('email')
    image = data.get('image')

    try:
        # If no fields to update were provided
        if not name and not email and not image:
            return jsonify({"status": "error", "message": "No fields to update were provided", "code": 400}), 400
        
        if not isinstance(current_user, Parent):
            return jsonify({"status": "error", "message": "User is not a parent", "code": 403}), 403

        # Find the Parent
        parent = session.query(Parent).filter_by(id=current_user.id).first()
        if not parent:
            return jsonify({"status": "error", "message": "Parent not found", "code": 404}), 404

        # If an email was provided, validate it
        if email and not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email Format", "code": 400}), 400
        
        if session.query(User).filter_by(email=email).first():
            return jsonify({"status": "error", "message": "A user with this email already exists", "code": 403}), 403
        
        # Update the parent's profile
        parent.update_profile(session=session, name=name, email=email, image=image)
        return jsonify({"status": "success", "message": "Parent updated", "code": 200}), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while updating the parent", "code": 500}), 500

    finally:
        session.close()

### Student Endpoints ###

@app.route('/students', methods=['POST'])
def register_student():
    session = SessionLocal()
    data = request.json

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    image = data.get('image')
    
    try:
        if not name or not email or not password or not image:
            return jsonify({"status": "error", "message": "Missing required fields", "code": 400}), 400
        
        if len(name) > 60:
            return jsonify({"status": "error", "message": "Name too long", "code": 400}), 400
        
        if not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email", "code": 400}), 400

        # Check if a student with this email already exists
        existing_user = session.query(User).filter_by(email=email).first()
        
        if existing_user:
            return jsonify({"status": "error", "message": "A user with this email already exists", "code": 400}), 400

        new_student = Student(name=name, email=email, password=password, image=image)

        session.add(new_student)
        session.commit()
        return jsonify({"status": "success", "message": "Student created", "code": 201}), 201

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while creating the student", "code": 500}), 500

    finally:
        session.close()

@app.route('/students', methods=['PUT'])
@login_required
def update_student():
    session = SessionLocal()
    data = request.json

    name = data.get('name')
    email = data.get('email')
    image = data.get('image')

    try:
        # If no fields to update were provided
        if not name and not email and not image:
            return jsonify({"status": "error", "message": "No fields to update were provided", "code": 400}), 400
        
        if not isinstance(current_user, Student):
            return jsonify({"status": "error", "message": "User is not a student", "code": 403}), 403

        # Find the student
        student = session.query(Student).filter_by(id=current_user.id).first()
        if not student:
            return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404

        # If an email was provided, validate it
        if email and not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email Format", "code": 400}), 400
        
        if session.query(User).filter_by(email=email).first():
            return jsonify({"status": "error", "message": "A user with this email already exists", "code": 403}), 403
        
        # Update the student's profile
        student.update_profile(session=session, name=name, email=email, image=image)
        return jsonify({"status": "success", "message": "Student updated", "code": 200}), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while updating the student", "code": 500}), 500

    finally:
        session.close()



### Class Endpoints ###
@app.route('/classes/<int:class_id>/students', methods=['GET'])
@login_required
def get_students(class_id):
    session = SessionLocal()
    try:
        if not isinstance(current_user, Teacher):
            return jsonify({"status": "error", "message": "Unauthorized", "code": 403}), 403 

        # Check if the logged in user is the teacher of the class
        teacher_class = session.query(Class).filter_by(id=class_id, teacher_id=current_user.id).first()
        if not teacher_class:
            return jsonify({"status": "error", "message": "Unauthorized", "code": 403}), 403

        students = teacher_class.students

        # Transform students list into JSON serializable format
        students_json = [
            {
                'name': student.name,
                'email': student.email,
            }
            for student in students
        ]

        return jsonify({"status": "success", "students": students_json, "code": 200}), 200
    
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while adding the student to the class", "code": 500}), 500
    
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

@app.route('/classes/<int:class_id>/students/<int:student_id>', methods=['DELETE'])
@login_required
def remove_student_from_class(class_id, student_id):
    session = SessionLocal()
    
    try:
        # Check if the logged in user is the teacher of the class
        teacher_class = session.query(Class).filter_by(id=class_id, teacher_id=current_user.get_id()).first()
        if not teacher_class:
            return jsonify({"status": "error", "message": "Unauthorized", "code": 403}), 403

        student = session.query(Student).filter_by(id=student_id).first()
        if not student:
            return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404

        # Remove student from class
        teacher_class.students.remove(student)
        session.commit()

        return jsonify({"status": "success", "message": "Student removed from class", "code": 200}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while removing the student from the class", "code": 500}), 500
    finally:
        session.close()

@app.route('/classes/<int:class_id>/students/<int:student_id>', methods=['GET'])
@login_required
def get_student_profile(class_id, student_id):
    # Get the current user from Flask-Login
    current_user = current_user()

    session = SessionLocal()

    try:
        # If the current user is a teacher, they can view the profile of the student who is in their class
        if isinstance(current_user, Teacher):
            # Find the class
            class_ = session.query(Class).filter_by(id=class_id, teacher_id=current_user.id).first()
            if not class_:
                return jsonify({"status": "error", "message": "Class not found", "code": 404}), 404

            # Get the student's profile
            student_profile = current_user.get_student_profile(session=session, student_id=student_id)
            if not student_profile:
                return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404

        # If the current user is a parent, they can view the profile of their children
        elif isinstance(current_user, Parent):
            # Get the child's profile
            student_profile = current_user.get_child_profile(session=session, student_id=student_id)
            if not student_profile:
                return jsonify({"status": "error", "message": "Student not found or you are not the parent of this student", "code": 404}), 404

        else:
            return jsonify({"status": "error", "message": "Unauthorized access", "code": 403}), 403

        # Create the response
        response = {
            "status": "success",
            "data": student_profile,
            "code": 200
        }
        return jsonify(response), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"status": "error", "message": "An error occurred", "code": 500}), 500

    finally:
        session.close()

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    app.run(debug=True)

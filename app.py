from flask import Flask, request, jsonify, g
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from Models import Base, Teacher, Class, User, Student, Parent, ConnectionRequest, student_class_association, parent_student_association
from Helpers import is_valid_email
import bcrypt
import os
import imghdr

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

app.config.from_object('config.ProductionConfig')

# specify the path where you want to save your images
UPLOAD_FOLDER = './images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# limit the maximum file size to 1MB
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB

# Create the SQLAlchemy engine
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.before_request
def create_session():
    g.session = SessionLocal()

@app.teardown_appcontext
def close_session(exception=None):
    session = g.pop('session', None)
    if session is not None:
        session.close()

@login_manager.user_loader
def load_user(user_id):
    return g.session.get(User, user_id)

##### User Endpoints #####

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = g.session.query(User).filter_by(email=email).first()

    if not is_valid_email(email):
        return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400 
    
    if user is None:
        return jsonify({"status": "error", "message": "Email could not be found", "code": 403}), 403
    
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
    try:
        user = g.session.query(User).filter_by(id=current_user.id).first()
        
        if not user:
            return jsonify({"status": "error", "message": "User not found", "code": 404}), 404
        
        g.session.delete(user)
        g.session.commit()

        logout_user()

        return jsonify({"status": "success", "message": "User successfully deleted", "code": 200}), 200
    
    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while deleting the user", "code": 500}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part", "code": 400}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file", "code": 400}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # after saving the file, check that it's a valid image
        image_type = imghdr.what(file_path)
        if not image_type:
            os.remove(file_path)  # remove the file if it's not a valid image
            return jsonify({"status": "error", "message": "Not a valid image", "code": 400}), 400

        return jsonify({"status": "success", "message": "File uploaded successfully", "code": 200}), 200
    return jsonify({"status": "error", "message": "File type not allowed", "code": 400}), 400

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/teacher/classes/<int:class_id>/send', methods=['POST'])
@login_required
def teacher_send_request_to_student(class_id):
    recipient_email = request.json.get('email')

    try:
        if not isinstance(current_user, Teacher):
            return jsonify({"status": "error", "message": "Not authorized", "code": 403}), 403
        if not recipient_email:
            return jsonify({"status": "error", "message": "No student email provided", "code": 400}), 400
        if not is_valid_email(recipient_email):
            return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

        recipient = g.session.query(Student).filter_by(email=recipient_email).first()
        if not recipient:
            return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404
        
        class_ = g.session.query(Class).filter_by(id=class_id, teacher_id=current_user.id).first()
        if not class_:
            return jsonify({"status": "error", "message": "Class not found or not belonging to the current user", "code": 404}), 404

        if g.session.query(student_class_association).filter_by(student_id=recipient.id, class_id=class_.id).first() is not None:
            return jsonify({"status": "error", "message": "The student is already a member of this class", "code": 400}), 400

        # Check if there is any existing request that is the exact same.
        existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=current_user.id, recipient_id=recipient.id, class_id=class_id).first()
        if existing_request and existing_request.status == 'pending':
            return jsonify({"status": "error", "message": "Request is already pending", "code": 400}), 400
        
        student_existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=recipient.id, recipient_id=current_user.id, class_id=class_id).first()
        if student_existing_request and student_existing_request.status == 'pending':
            class_.students.append(recipient)
            student_existing_request.status = 'accepted'
            return jsonify({"status": "success", "message": "Request accepted", "code": 200}), 200

        new_request = ConnectionRequest(sender_id=current_user.id, recipient_id=recipient.id, class_id=class_id, type='class_invitation')
        g.session.add(new_request)
        g.session.commit()

        return jsonify({"status": "success", "message": "Invite sent successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500


@app.route('/students/requests/<int:request_id>/respond', methods=['POST'])
@login_required
def student_respond_to_teacher_request(request_id):
    response = request.json.get('response')

    try:
        if not response:
            return jsonify({"status": "error", "message": "No response provided", "code": 400}), 400
        if not isinstance(current_user, Student):
            return jsonify({"status": "error", "message": "Forbidden: Unauthorized", "code": 403}), 403 

        connection_request = g.session.query(ConnectionRequest).filter_by(id=request_id, recipient_id=current_user.id).first()
        if not connection_request:
            return jsonify({"status": "error", "message": "Request not found", "code": 404}), 404
        
        if connection_request.type != 'class_invitation':
            return jsonify({"status": "error", "message": "Request not a class invitation", "code": 404}), 404
        
        if connection_request.status != "pending":
            return jsonify({"status": "error", "message": "Request already processed.", "code": 404}), 404

        if response == 'accept':
            class_ = g.session.query(Class).filter_by(id=connection_request.class_id).first()
            if not class_:
                return jsonify({"status": "error", "message": "Class not found", "code": 404}), 404

            class_.students.append(current_user._get_current_object())
            connection_request.status = 'accepted'
            g.session.commit()
            return jsonify({"status": "success", "message": "Request accepted", "code": 200}), 200

        elif response == 'reject':
            connection_request.status = 'rejected'
            g.session.commit()
            return jsonify({"status": "success", "message": "Request rejected", "code": 200}), 200

        else:
            return jsonify({"status": "error", "message": "Invalid response", "code": 400}), 400

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500

@app.route('/students/classes/join', methods=['POST'])
@login_required
def student_join_class():
    class_code = request.json.get('code')

    try:
        if not class_code:
            return jsonify({"status": "error", "message": "No class code provided", "code": 400}), 400
        if not isinstance(current_user, Student):
            return jsonify({"status": "error", "message": "Not authorized", "code": 403}), 403
        class_ = g.session.query(Class).filter_by(class_code=class_code).first()
        if not class_:
            return jsonify({"status": "error", "message": "Class not found", "code": 404}), 404
        if g.session.query(student_class_association).filter_by(student_id=current_user.id, class_id=class_.id).first() is not None:
            return jsonify({"status": "error", "message": "You're already a member of this class", "code": 400}), 400

        existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=current_user.id, class_id=class_.id).first()
        if existing_request and existing_request.status == 'pending':
            return jsonify({"status": "error", "message": "Request is already pending", "code": 400}), 400
        
        teacher_existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=class_.teacher_id, recipient_id=current_user.id, class_id=class_.id).first()
        if teacher_existing_request and teacher_existing_request.status == 'pending':
            class_.students.append(current_user._get_current_object())
            teacher_existing_request.status = 'accepted'
            return jsonify({"status": "success", "message": "Request accepted", "code": 200}), 200

        new_request = ConnectionRequest(sender_id=current_user.id, recipient_id=class_.teacher_id, class_id=class_.id, type='join_request')
        g.session.add(new_request)
        g.session.commit()

        return jsonify({"status": "success", "message": "Join request sent successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500

@app.route('/teachers/requests/<int:request_id>/respond', methods=['POST'])
@login_required
def teacher_respond_to_student_request(request_id):
    response = request.json.get('response')

    try:
        if not response:
            return jsonify({"status": "error", "message": "No response provided", "code": 400}), 400 
        if not isinstance(current_user, Teacher):
            return jsonify({"status": "error", "message": "Forbidden: Unauthorized", "code": 403}), 403 
        connection_request = g.session.query(ConnectionRequest).filter_by(id=request_id, recipient_id=current_user.id).first()
        if not connection_request:
            return jsonify({"status": "error", "message": "Request not found", "code": 404}), 404
        
        if connection_request.type != 'join_request':
            return jsonify({"status": "error", "message": "Request not a join request", "code": 404}), 404
        
        if connection_request.status != "pending":
            return jsonify({"status": "error", "message": "Request already processed.", "code": 404}), 404

        if response == 'accept':
            class_ = g.session.query(Class).filter_by(id=connection_request.class_id, teacher_id=current_user.id).first()
            if not class_:
                return jsonify({"status": "error", "message": "Class not found or not belonging to the current user", "code": 404}), 404

            student = g.session.query(Student).filter_by(id=connection_request.sender_id).first()
            if not student:
                return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404

            class_.students.append(student)
            connection_request.status = 'accepted'
            g.session.commit()
            return jsonify({"status": "success", "message": "Request accepted", "code": 200}), 200

        elif response == 'reject':
            connection_request.status = 'rejected'
            g.session.commit()
            return jsonify({"status": "success", "message": "Request rejected", "code": 200}), 200

        else:
            return jsonify({"status": "error", "message": "Invalid response", "code": 400}), 400

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500


@app.route('/parents/students/send', methods=['POST'])
@login_required
def parent_send_child_request():
    recipient_email = request.json.get('email')

    try:
        if not isinstance(current_user, Parent):
            return jsonify({"status": "error", "message": "Not authorized", "code": 403}), 403
        if not recipient_email:
            return jsonify({"status": "error", "message": "No student email provided", "code": 400}), 400
        if not is_valid_email(recipient_email):
            return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400 
        recipient = g.session.query(Student).filter_by(email=recipient_email).first()
        if not recipient:
            return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404
        if g.session.query(parent_student_association).filter_by(parent_id=current_user.id, student_id=recipient.id).first() is not None:
            return jsonify({"status": "error", "message": "The student is already listed as a child", "code": 400}), 400

        # Check if there is any existing request that is the exact same.
        existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=current_user.id, recipient_id=recipient.id).first()
        if existing_request and existing_request.status == 'pending':
            return jsonify({"status": "error", "message": "Request is already pending", "code": 400}), 400

        new_request = ConnectionRequest(sender_id=current_user.id, recipient_id=recipient.id, type='parent_to_child')
        g.session.add(new_request)
        g.session.commit()

        return jsonify({"status": "success", "message": "Request sent successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500


@app.route('/students/parents/send', methods=['POST'])
@login_required
def student_send_parent_request():
    recipient_email = request.json.get('email')

    try:
        if not isinstance(current_user, Student):
            return jsonify({"status": "error", "message": "Not authorized", "code": 403}), 403
        if not recipient_email:
            return jsonify({"status": "error", "message": "No parent email provided", "code": 400}), 400
        if not is_valid_email(recipient_email):
            return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400 
        recipient = g.session.query(Parent).filter_by(email=recipient_email).first()
        if not recipient:
            return jsonify({"status": "error", "message": "Parent not found", "code": 404}), 404
        if g.session.query(parent_student_association).filter_by(parent_id=current_user.id, student_id=recipient.id).first() is not None:
            return jsonify({"status": "error", "message": "The user is already listed as a parent", "code": 400}), 400

        # Check if there is any existing request that is the exact same.
        existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=current_user.id, recipient_id=recipient.id).first()
        if existing_request and existing_request.status == 'pending':
            return jsonify({"status": "error", "message": "Request is already pending", "code": 400}), 400

        new_request = ConnectionRequest(sender_id=current_user.id, recipient_id=recipient.id, type='child_to_parent')
        g.session.add(new_request)
        g.session.commit()

        return jsonify({"status": "success", "message": "Request sent successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500


@app.route('/students/requests/<int:request_id>/respond', methods=['POST'])
@login_required
def student_respond_to_parent_request(request_id):
    response = request.json.get('response')

    try:
        if not isinstance(current_user, Student):
            return jsonify({"status": "error", "message": "Forbidden: Unauthorized", "code": 403}), 403 
        if not response:
            return jsonify({"status": "error", "message": "No response provided", "code": 400}), 400 
        connection_request = g.session.query(ConnectionRequest).filter_by(id=request_id, recipient_id=current_user.id).first()
        if not connection_request:
            return jsonify({"status": "error", "message": "Request not found", "code": 404}), 404
        if connection_request.type != 'parent_to_child':
            return jsonify({"status": "error", "message": "Request not a parent-child connection", "code": 404}), 404
        if connection_request.status != "pending":
            return jsonify({"status": "error", "message": "Request already processed.", "code": 404}), 404
        if response == 'accept':
            parent = g.session.query(Parent).filter_by(id=connection_request.sender_id).first()
            if not parent:
                return jsonify({"status": "error", "message": "Parent not found", "code": 404}), 404

            current_user._get_current_object().parents.append(parent)
            connection_request.status = 'accepted'
            g.session.commit()
            return jsonify({"status": "success", "message": "Request accepted", "code": 200}), 200

        elif response == 'reject':
            connection_request.status = 'rejected'
            g.session.commit()
            return jsonify({"status": "success", "message": "Request rejected", "code": 200}), 200

        else:
            return jsonify({"status": "error", "message": "Invalid response", "code": 400}), 400

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500


@app.route('/parents/requests/<int:request_id>/respond', methods=['POST'])
@login_required
def parent_respond_to_student_request(request_id):
    response = request.json.get('response')

    try:
        if not isinstance(current_user, Parent):
            return jsonify({"status": "error", "message": "Forbidden: Unauthorized", "code": 403}), 403 
        if not response:
            return jsonify({"status": "error", "message": "No response provided", "code": 400}), 400 
        connection_request = g.session.query(ConnectionRequest).filter_by(id=request_id, recipient_id=current_user.id).first()
        if not connection_request:
            return jsonify({"status": "error", "message": "Request not found", "code": 404}), 404
        if connection_request.type != 'child_to_parent':
            return jsonify({"status": "error", "message": "Request not a child-parent connection", "code": 404}), 404
        if connection_request.status != "pending":
            return jsonify({"status": "error", "message": "Request already processed.", "code": 404}), 404
        if response == 'accept':
            parent = g.session.query(Parent).filter_by(id=connection_request.sender_id).first()
            if not parent:
                return jsonify({"status": "error", "message": "Parent not found", "code": 404}), 404

            current_user._get_current_object().parents.append(parent)
            connection_request.status = 'accepted'
            g.session.commit()
            return jsonify({"status": "success", "message": "Request accepted", "code": 200}), 200

        elif response == 'reject':
            connection_request.status = 'rejected'
            g.session.commit()
            return jsonify({"status": "success", "message": "Request rejected", "code": 200}), 200

        else:
            return jsonify({"status": "error", "message": "Invalid response", "code": 400}), 400

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500


@app.route('/students/classes/<int:class_id>/leave', methods=['POST'])
@login_required
def student_leave_class(class_id):
    try:
        class_ = g.session.query(Class).filter_by(id=class_id).first()
        if not class_ or current_user._get_current_object() not in class_.students:
            return jsonify({"status": "error", "message": "Class not found or student not enrolled", "code": 404}), 404

        class_.students.remove(current_user._get_current_object())
        g.session.commit()

        return jsonify({"status": "success", "message": "Class left successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500

@app.route('/teachers/classes/<int:class_id>/remove/<int:student_id>', methods=['POST'])
@login_required
def teacher_remove_student_from_class(class_id, student_id):
    try:
        class_ = g.session.query(Class).filter_by(id=class_id, teacher_id=current_user.id).first()
        if not class_:
            return jsonify({"status": "error", "message": "Class not found or not belonging to the current user", "code": 404}), 404

        student = g.session.query(Student).filter_by(id=student_id).first()
        if not student or student not in class_.students:
            return jsonify({"status": "error", "message": "Student not found or not enrolled in the class", "code": 404}), 404

        class_.students.remove(student)
        g.session.commit()

        return jsonify({"status": "success", "message": "Student removed successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500

@app.route('/parents/students/<int:student_id>/remove', methods=['POST'])
@login_required
def parent_remove_student(student_id):
    try:
        student = g.session.query(Student).filter_by(id=student_id).first()
        if not student or student not in current_user._get_current_object().children:
            return jsonify({"status": "error", "message": "Student not found or not connected to the current user", "code": 404}), 404

        current_user._get_current_object().children.remove(student)
        g.session.commit()

        return jsonify({"status": "success", "message": "Student removed successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500

@app.route('/students/parents/<int:parent_id>/remove', methods=['POST'])
@login_required
def student_remove_parent(parent_id):
    try:
        parent = g.session.query(Parent).filter_by(id=parent_id).first()
        if not parent or current_user._get_current_object() not in parent.children:
            return jsonify({"status": "error", "message": "Parent not found or not connected to the student", "code": 404}), 404

        parent.children.remove(current_user._get_current_object())
        g.session.commit()

        return jsonify({"status": "success", "message": "Parent removed successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500

##### Teacher Endpoints #####

@app.route('/teachers', methods=['POST'])
def register_teacher():
    data = request.form

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    image_path = None  # Default value for image_path
    file = request.files.get('image')
    
    try:

        if not name or not email or not password:
            return jsonify({"status": "error", "message": "Missing required fields", "code": 400}), 400

        if len(name) > 60:
            return jsonify({"status": "error", "message": "Name too long", "code": 400}), 400
        
        if not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

        # Check if a teacher with this email already exists
        existing_user = g.session.query(User).filter_by(email=email).first()
        
        if existing_user:
            return jsonify({"status": "error", "message": "A user with this email already exists", "code": 409}), 409
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)

        # Hash password before saving        
        new_teacher = Teacher(name=name, email=email, password=password, image=image_path)

        g.session.add(new_teacher)
        g.session.commit()
        return jsonify({"status": "success", "message": "Teacher created", "code": 201}), 201

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while creating the teacher", "code": 500}), 500


@app.route('/teachers', methods=['PUT'])
@login_required
def update_teacher():
    data = request.form  # changed from request.json
    image = request.files['image'] if 'image' in request.files else None
    name = data.get('name')
    email = data.get('email')

    try:
        # If no fields to update were provided
        if not name and not email and image is None:
            return jsonify({"status": "error", "message": "No fields to update were provided", "code": 400}), 400
        
        if not isinstance(current_user._get_current_object(), Teacher):
            return jsonify({"status": "error", "message": "User is not a teacher", "code": 403}), 403
        
        if name and len(name) > 60:
            return jsonify({"status": "error", "message": "Name too long", "code": 400}), 400

        # Find the teacher
        teacher = g.session.query(Teacher).filter_by(id=current_user.id).first()
        if not teacher:
            return jsonify({"status": "error", "message": "Teacher not found", "code": 404}), 404

        # If an email was provided, validate it
        if email:
            if not is_valid_email(email):
                return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

            if g.session.query(User).filter(User.email==email, User.id!=current_user.id).first():
                return jsonify({"status": "error", "message": "A user with this email already exists", "code": 403}), 403
        
        # If an image was provided, validate it, save it and get its path
        image_path = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

        # Update the teacher's profile
        teacher.update_profile(session=g.session, name=name, email=email, image=image_path)
        return jsonify({"status": "success", "message": "Teacher updated", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while updating the teacher", "code": 500}), 500


### Class/Teacher Endpoints ###
@app.route('/classes', methods=['POST'])
@login_required
def create_class():

    try:
        data = request.json
        class_name = data.get('class_name')

        # Check if user is a teacher
        if not isinstance(current_user, Teacher):
            return jsonify({"status": "error", "message": "User is not a teacher", "code": 403}), 403

        # Check if the teacher exists
        teacher = g.session.query(Teacher).filter_by(id=current_user.id).first()
        if not teacher:
            return jsonify({"status": "error", "message": "Teacher not found", "code": 404}), 404
        
        if not class_name:
            return jsonify({"status": "error", "message": "Missing class name", "code": 400}), 400
        
        if len(class_name) > 60:
            return jsonify({"status": "error", "message": "Class name too long", "code": 400}), 400

        # Check if a class with this name already exists for this teacher
        existing_class = g.session.query(Class).filter_by(class_name=class_name, teacher_id=teacher.id).first()
        if existing_class:
            return jsonify({"status": "error", "message": "A class with this name already exists for this teacher", "code": 409}), 409

        new_class = Class(teacher_id=teacher.id, class_name=class_name)

        g.session.add(new_class)
        g.session.commit()
        return jsonify({"status": "success", "message": "Class created", "code": 201}), 201

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while creating the class", "code": 500}), 500


@app.route('/classes/<int:class_id>', methods=['DELETE'])
@login_required
def delete_class(class_id):
    try:
        # Find the class with the given id
        class_ = g.session.query(Class).filter_by(id=class_id).first()

        # If the class doesn't exist
        if not class_:
            return jsonify({"status": "error", "message": "Class not found", "code": 404}), 404

        # If the logged in user is not the teacher of this class
        if class_.teacher_id != current_user.id:
            return jsonify({"status": "error", "message": "You are not the teacher of this class", "code": 403}), 403

        # Delete the class
        g.session.delete(class_)
        g.session.commit()
        return jsonify({"status": "success", "message": "Class successfully deleted", "code": 200}), 200
    
    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while deleting the class", "code": 500}), 500


### Parent Endpoints ###

@app.route('/parents', methods=['POST'])
def register_parent():
    data = request.form

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    image_path = None  # Default value for image_path
    file = request.files.get('image')
    
    try:
        if not name or not email or not password:
            return jsonify({"status": "error", "message": "Missing required fields", "code": 400}), 400
        
        if len(name) > 60:
            return jsonify({"status": "error", "message": "Name too long", "code": 400}), 400
        
        if not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

        # Check if a parent with this email already exists
        existing_user = g.session.query(User).filter_by(email=email).first()
        
        if existing_user:
            return jsonify({"status": "error", "message": "A user with this email already exists", "code": 409}), 409
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)

        new_parent = Parent(name=name, email=email, password=password, image=image_path)

        g.session.add(new_parent)
        g.session.commit()
        return jsonify({"status": "success", "message": "Parent created", "code": 201}), 201

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while creating the parent", "code": 500}), 500


@app.route('/parents', methods=['PUT'])
def update_parent():
    data = request.form

    name = data.get('name')
    email = data.get('email')
    image = request.files['image'] if 'image' in request.files else None

    try:
        # If no fields to update were provided
        if not name and not email and not image:
            return jsonify({"status": "error", "message": "No fields to update were provided", "code": 400}), 400

        if name and len(name) > 60:
            return jsonify({"status": "error", "message": "Name too long", "code": 400}), 400
        
        if not isinstance(current_user, Parent):
            return jsonify({"status": "error", "message": "User is not a parent", "code": 403}), 403

        # Find the Parent
        parent = g.session.query(Parent).filter_by(id=current_user.id).first()
        if not parent:
            return jsonify({"status": "error", "message": "Parent not found", "code": 404}), 404

       # If an email was provided, validate it
        if email:
            if not is_valid_email(email):
                return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

            if g.session.query(User).filter(User.email==email, User.id!=current_user.id).first():
                return jsonify({"status": "error", "message": "A user with this email already exists", "code": 403}), 403
        
        # If an image was provided, validate it, save it and get its path
        image_path = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
        
        # Update the parent's profile
        parent.update_profile(session=g.session, name=name, email=email, image=image_path)
        return jsonify({"status": "success", "message": "Parent updated", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while updating the parent", "code": 500}), 500


@app.route('/children', methods=['GET'])
@login_required
def get_children():
    if not isinstance(current_user, Parent):
        return jsonify({"status": "error", "message": "Access forbidden", "code": 403}), 403

    try:
        parent = g.session.query(Parent).filter_by(id=current_user.id).first()

        if parent is None:
            return jsonify({"status": "error", "message": "Parent not found", "code": 404}), 404

        children = [child.name for child in parent.children]
        return jsonify({"status": "success", "children": children, "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        return jsonify({"status": "error", "message": "An error occurred", "code": 500}), 500


### Student Endpoints ###

@app.route('/students', methods=['POST'])
def register_student():
    data = request.form

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    file = request.files.get('image')
    
    try:
        if not name or not email or not password or not file:
            return jsonify({"status": "error", "message": "Missing required fields", "code": 400}), 400
        
        if len(name) > 60:
            return jsonify({"status": "error", "message": "Name too long", "code": 400}), 400
        
        if not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

        # Check if a student with this email already exists
        existing_user = g.session.query(User).filter_by(email=email).first()
        
        if existing_user:
            return jsonify({"status": "error", "message": "A user with this email already exists", "code": 409}), 409
        
        if not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Invalid file type", "code": 400}), 400
        
        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        new_student = Student(name=name, email=email, password=password, image=image_path)

        g.session.add(new_student)
        g.session.commit()
        return jsonify({"status": "success", "message": "Student created", "code": 201}), 201

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while creating the student", "code": 500}), 500
    
    except ValueError as e:
        app.logger.error(f"ValueError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Cannot recognize a face from the image", "code": 422}), 422


@app.route('/students', methods=['PUT'])
@login_required
def update_student():
    data = request.form

    name = data.get('name')
    email = data.get('email')
    image = request.files['image'] if 'image' in request.files else None

    try:
        # If no fields to update were provided
        if not name and not email and not image:
            return jsonify({"status": "error", "message": "No fields to update were provided", "code": 400}), 400
        
        if name and len(name) > 60:
            return jsonify({"status": "error", "message": "Name too long", "code": 400}), 400
        
        if not isinstance(current_user, Student):
            return jsonify({"status": "error", "message": "User is not a student", "code": 403}), 403

        # Find the student
        student = g.session.query(Student).filter_by(id=current_user.id).first()
        if not student:
            return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404

        # If an email was provided, validate it
        if email:
            if not is_valid_email(email):
                return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

            if g.session.query(User).filter(User.email==email, User.id!=current_user.id).first():
                return jsonify({"status": "error", "message": "A user with this email already exists", "code": 403}), 403
            
        # If an image was provided, validate it, save it and get its path
        image_path = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
        
        # Update the student's profile
        student.update_profile(session=g.session, name=name, email=email, image=image_path)
        return jsonify({"status": "success", "message": "Student updated", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while updating the student", "code": 500}), 500
    
    except ValueError as e:
        app.logger.error(f"ValueError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Cannot recognize a face from the image", "code": 422}), 422


@app.route('/classes', methods=['GET'])
@login_required
def get_classes():
    if isinstance(current_user, Parent):
            return jsonify({"status": "error", "message": "Access forbidden", "code": 403}), 403
    try:
        if isinstance(current_user, Student):
            student = g.session.query(Student).filter_by(id=current_user.id).first()

            if student is None:
                return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404

            classes = [{"id": _class.id, "name": _class.class_name} for _class in student.classes]
            return jsonify({"status": "success", "classes": classes, "code": 200}), 200
        elif isinstance(current_user, Teacher):
            teacher = g.session.query(Teacher).filter_by(id=current_user.id).first()

            if teacher is None:
                return jsonify({"status": "error", "message": "Teacher not found", "code": 404}), 404

            classes = [{"id": _class.id, "name": _class.class_name} for _class in teacher.classes]
            return jsonify({"status": "success", "classes": classes, "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        return jsonify({"status": "error", "message": "An error occurred", "code": 500}), 500


### Class Endpoints ###
@app.route('/classes/<int:class_id>/students', methods=['GET'])
@login_required
def get_students(class_id):
    try:
        if not isinstance(current_user, Teacher):
            return jsonify({"status": "error", "message": "Unauthorized", "code": 403}), 403 

        # Check if the logged in user is the teacher of the class
        teacher_class = g.session.query(Class).filter_by(id=class_id, teacher_id=current_user.id).first()
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
        app.logger.error(f"SQLAlchemyError: {e}")
        return jsonify({"status": "error", "message": "An error occurred while adding the student to the class", "code": 500}), 500


@app.route('/classes/<int:class_id>/students/<int:student_id>', methods=['GET'])
@login_required
def get_student_profile(class_id, student_id):
    # Get the current user from Flask-Login

    try:
        # If the current user is a teacher, they can view the profile of the student who is in their class
        if isinstance(current_user, Teacher):
            # Find the class
            class_ = g.session.query(Class).filter_by(id=class_id, teacher_id=current_user.id).first()
            if not class_:
                return jsonify({"status": "error", "message": "Class not found", "code": 404}), 404

            # Get the student's profile
            student_profile = current_user.get_student_profile(session=g.session, student_id=student_id)
            if not student_profile:
                return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404

        # If the current user is a parent, they can view the profile of their children
        elif isinstance(current_user, Parent):
            # Get the child's profile
            student_profile = current_user.get_child_profile(session=g.session, student_id=student_id)
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
        app.logger.error(f"SQLAlchemyError: {e}")
        return jsonify({"status": "error", "message": "An error occurred", "code": 500}), 500


@app.route('/classes/<int:class_id>', methods=['GET'])
@login_required
def get_class_code(class_id):
    try:
        if isinstance(current_user, Parent):
            return jsonify({"status": "error", "message": "Unauthorized: Forbidden", "code": 403}), 403
        elif isinstance(current_user, Student):
            if not g.session.query(student_class_association).filter_by(student_id=current_user.id, class_id=class_.id).first() is not None:
                return jsonify({"status": "error", "message": "Unauthorized: Forbidden", "code": 403}), 403
        elif isinstance(current_user, Teacher):
            teacher_class = g.session.query(Class).filter_by(id=class_id, teacher_id=current_user.id).first()
            if not teacher_class:
                return jsonify({"status": "error", "message": "Unauthorized", "code": 403}), 403
        
        class_ = g.session.query(Class).filter_by(id=class_id).first()
        if not class_:
            return jsonify({"status": "error", "message": "Class not found", "code": 404}), 404

        # Create the response
        response = {
            "status": "success",
            "data": class_.class_code,
            "code": 200
        }
        return jsonify(response), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        return jsonify({"status": "error", "message": "An error occurred", "code": 500}), 500


if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    app.run(debug=True)

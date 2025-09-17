from flask import Flask, request, jsonify, g, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from Models import (Base, Teacher, Class, User, 
                    Student, Parent, ConnectionRequest, 
                    student_class_association, 
                    parent_student_association)
from Helpers import is_valid_email
from datetime import timedelta
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_refresh_token,
    jwt_required, get_jwt, get_jwt_identity,
    create_access_token, verify_jwt_in_request,
    decode_token)
import bcrypt
import os
import imghdr
from functools import wraps
from config import CORS_ORIGIN

app = Flask(__name__)
cfg_name = os.getenv("FLASK_CONFIG", "Production")
app.config.from_object(f"config.{cfg_name}Config")

CORS(app,
     resources={r"/*": {"origins": CORS_ORIGIN}},
     supports_credentials=True)

##### JWT SETUP #####

jwt = JWTManager(app)
# in memory blocklist for demo -> we can switch to redis later
TOKEN_BLOCKLIST = set()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_headers, jwt_payload):
    return jwt_payload.get("jti") in TOKEN_BLOCKLIST

@jwt.unauthorized_loader
def _unauth(msg):
    return jsonify({"status": "error","message": "Missing or invalid credentials","code": 401}), 401

@jwt.invalid_token_loader
def _invalid(msg):
    return jsonify({"status": "error","message": "Invalid token","code": 401}), 401

@jwt.expired_token_loader
def _expired(jwt_header, jwt_payload):
    return jsonify({"status": "error","message": "Token expired","code": 401}), 401

def set_access_cookie(resp, access_token):
    resp.set_cookie(
        "access_token", access_token,
        httponly=True, secure=False, samesite="Lax",
        max_age=60*60  # 1 hour
    )

def set_refresh_cookie(resp, refresh_token):
    resp.set_cookie(
        "refresh_token", refresh_token,
        httponly=True, secure=False, samesite="Lax",
        max_age=60*60*24*7  # 7 days
    )

def clear_auth_cookies(resp):
    resp.set_cookie("access_token", "", expires=0)
    resp.set_cookie("refresh_token", "", expires=0)

def role_required(*roles):
    """Enforce role from JWT custom claim."""
    def wrapper(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            verify_jwt_in_request()
            if get_jwt().get("role") not in roles:
                return jsonify({"status":"error","message":"Forbidden","code":403}), 403
            return fn(*args, **kwargs)
        return inner
    return wrapper


##### FILE UPLOADS #####

# specify the path where you want to save your images
UPLOAD_FOLDER = './images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# limit the maximum file size to 1MB
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB

##### SQLALCHEMY #####
# Create the SQLAlchemy engine
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.before_request
def create_session():
    g.session = SessionLocal()

    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        role = get_jwt().get("role") if uid else None
    except Exception:
        uid, role = None, None

    g.role, g.user = None, None
    if uid:
        if role == "teacher":
            g.role, g.user = "teacher", g.session.get(Teacher, uid)
        elif role == "student":
            g.role, g.user = "student", g.session.get(Student, uid)
        elif role == "parent":
            g.role, g.user = "parent", g.session.get(Parent, uid)
        else:
            g.role, g.user = "user", g.session.get(User, uid)

@app.teardown_appcontext
def close_session(exception=None):
    session = g.pop('session', None)
    if session is not None:
        session.close()

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

##### AUTH #####

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not is_valid_email(email):
        return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400 

    user = g.session.query(User).filter_by(email=email).first()

    if user is None:
        return jsonify({"status": "error", "message": "Email could not be found", "code": 403}), 403
    
    if not bcrypt.checkpw(password.encode('utf-8'), user.password):
        return jsonify({"status": "error", "message": "Incorrect password", "code": 403}), 403
    
    role = "user"
    if isinstance(user, Teacher):
        role = "teacher"
    elif isinstance(user, Student):
        role = "student"
    elif isinstance(user, Parent):
        role = "parent"
    
    claims = {"role": role, "name": user.name}

    access = create_access_token(identity=user.id, additional_claims=claims)
    refresh = create_refresh_token(identity=user.id, additional_claims=claims)

    resp = jsonify({"status": "success", "message": "Login successful", "code": 200})
    set_access_cookie(resp, access)
    set_refresh_cookie(resp, refresh)
    
    return resp, 200

@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True, locations=['cookies', 'headers'])
def auth_refresh():
    claims = get_jwt()
    uid = get_jwt_identity()
    new_access = create_access_token(identity=uid, additional_claims={
        "role": claims.get("role"),
        "name": claims.get("name")
    })
    resp = jsonify({"status": "success", "message": "Token refreshed", "code": 200})
    set_access_cookie(resp, new_access)
    return resp, 200

@app.route('/api/auth/logout', methods=['POST'])
@jwt_required(optional=True)
def auth_logout():
    j = get_jwt()
    if j:
        TOKEN_BLOCKLIST.add(j["jti"])
    rt = request.cookies.get("refresh_token")
    if rt:
        try:
            payload = decode_token(rt)
            TOKEN_BLOCKLIST.add(payload["jti"])
        except Exception:
            pass
    resp = jsonify({"status": "success", "message": "Logged out", "code": 200})
    clear_auth_cookies(resp)
    return resp, 200

@app.route('/api/users', methods=['DELETE'])
def delete_user():
    try:
        if not g.user:
            return jsonify({"status": "error", "message": "User not found", "code": 404}), 404
        
        g.session.delete(g.user)
        g.session.commit()

        resp = jsonify({"status": "success", "message": "User successfully deleted", "code": 200})
        clear_auth_cookies(resp)

        return resp, 200
    
    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while deleting the user", "code": 500}), 500

@app.route('/api/me', methods=['GET'])
@jwt_required()
def me():
    j = get_jwt()
    return jsonify({
        "status":"success",
        "user": {"id": get_jwt_identity(), "role": j.get("role"), "name": j.get("name")}
    }), 200
    
##### UPLOAD #####

@app.route('/api/upload', methods=['POST'])
@jwt_required()
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

##### TEACHER <-> Student #####
@app.route('/api/teachers/classes/<int:class_id>/requests', methods=['POST'])
@jwt_required()
@role_required("teacher")
def teacher_send_request_to_student(class_id):
    recipient_email = (request.get_json() or {}).get("email")

    try:
        if not recipient_email or not is_valid_email(recipient_email):
            return jsonify({"status": "error", "message": "No student email provided", "code": 400}), 400

        teacher = g.user
        recipient = g.session.query(Student).filter_by(email=recipient_email).first()
        if not recipient:
            return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404
        
        class_ = g.session.query(Class).filter_by(id=class_id, teacher_id=teacher.id).first()
        if not class_:
            return jsonify({"status": "error", "message": "Class not found or not belonging to the current user", "code": 404}), 404

        if g.session.query(student_class_association).filter_by(student_id=recipient.id, class_id=class_.id).first() is not None:
            return jsonify({"status": "error", "message": "The student is already a member of this class", "code": 400}), 400

        # Check if there is any existing request that is the exact same.
        existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=teacher.id, recipient_id=recipient.id, class_id=class_id).first()
        if existing_request and existing_request.status == 'pending':
            return jsonify({"status": "error", "message": "Request is already pending", "code": 400}), 400
        
        student_existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=recipient.id, recipient_id=teacher.id, class_id=class_id).first()
        if student_existing_request and student_existing_request.status == 'pending':
            class_.students.append(recipient)
            student_existing_request.status = 'accepted'
            return jsonify({"status": "success", "message": "Request accepted", "code": 200}), 200

        new_request = ConnectionRequest(sender_id=teacher.id, recipient_id=recipient.id, class_id=class_id, type='class_invitation')
        g.session.add(new_request)
        g.session.commit()

        return jsonify({"status": "success", "message": "Invite sent successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500


@app.route('/api/students/classes/requests/<int:request_id>', methods=['PATCH'])
@jwt_required()
@role_required("student")
def student_respond_to_teacher_request(request_id):
    response = (request.get_json() or {}).get('response')

    try:
        if not response:
            return jsonify({"status": "error", "message": "No response provided", "code": 400}), 400
        
        student = g.user

        connection_request = g.session.query(ConnectionRequest).filter_by(id=request_id, recipient_id=student.id).first()
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

@app.route('/api/students/classes/<int:class_id>/requests', methods=['POST'])
@jwt_required()
@role_required("student")
def student_join_class():
    class_code = (request.get_json() or {}).get('code')

    try:
        if not class_code:
            return jsonify({"status": "error", "message": "No class code provided", "code": 400}), 400
        
        student = g.user
        class_ = g.session.query(Class).filter_by(class_code=class_code).first()    
        if not class_:
            return jsonify({"status": "error", "message": "Class not found", "code": 404}), 404
        if g.session.query(student_class_association).filter_by(student_id=student.id, class_id=class_.id).first() is not None:
            return jsonify({"status": "error", "message": "You're already a member of this class", "code": 400}), 400

        existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=student.id, class_id=class_.id).first()
        if existing_request and existing_request.status == 'pending':
            return jsonify({"status": "error", "message": "Request is already pending", "code": 400}), 400
        
        teacher_existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=class_.teacher_id, recipient_id=student.id, class_id=class_.id).first()
        if teacher_existing_request and teacher_existing_request.status == 'pending':
            class_.students.append(student)
            teacher_existing_request.status = 'accepted'
            return jsonify({"status": "success", "message": "Request accepted", "code": 200}), 200

        new_request = ConnectionRequest(sender_id=student.id, recipient_id=class_.teacher_id, class_id=class_.id, type='join_request')
        g.session.add(new_request)
        g.session.commit()

        return jsonify({"status": "success", "message": "Join request sent successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500

@app.route('/api/teacher/classes/<int:class_id>/requests/<int:request_id>', methods=['PATCH'])
@jwt_required()
@role_required("teacher")
def teacher_respond_to_student_request(request_id):
    response = (request.get_json() or {}).get('response')

    try:
        if not response:
            return jsonify({"status": "error", "message": "No response provided", "code": 400}), 400 
        
        teacher = g.user
        connection_request = g.session.query(ConnectionRequest).filter_by(id=request_id, recipient_id=teacher.id).first()
        if not connection_request:
            return jsonify({"status": "error", "message": "Request not found", "code": 404}), 404
        
        if connection_request.type != 'join_request':
            return jsonify({"status": "error", "message": "Request not a join request", "code": 404}), 404
        
        if connection_request.status != "pending":
            return jsonify({"status": "error", "message": "Request already processed.", "code": 404}), 404

        if response == 'accept':
            class_ = g.session.query(Class).filter_by(id=connection_request.class_id, teacher_id=teacher.id).first()
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


##### PARENT <-> STUDENT #####

@app.route('/api/parents/family/requests/', methods=['POST'])
@jwt_required()
@role_required("parent")
def parent_send_child_request():
    recipient_email = (request.get_json() or {}).get('email')

    try:
        if not recipient_email:
            return jsonify({"status": "error", "message": "No student email provided", "code": 400}), 400
        
        if not is_valid_email(recipient_email):
            return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400 
        
        parent = g.user
        recipient = g.session.query(Student).filter_by(email=recipient_email).first()
        if not recipient:
            return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404
        if g.session.query(parent_student_association).filter_by(parent_id=parent.id, student_id=recipient.id).first() is not None:
            return jsonify({"status": "error", "message": "The student is already listed as a child", "code": 400}), 400

        # Check if there is any existing request that is the exact same.
        existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=parent.id, recipient_id=recipient.id).first()
        if existing_request and existing_request.status == 'pending':
            return jsonify({"status": "error", "message": "Request is already pending", "code": 400}), 400

        new_request = ConnectionRequest(sender_id=parent.id, recipient_id=recipient.id, type='parent_to_child')
        g.session.add(new_request)
        g.session.commit()

        return jsonify({"status": "success", "message": "Request sent successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500


@app.route('/api/students/family/requests/', methods=['POST'])
@jwt_required()
@role_required("student")
def student_send_parent_request():
    recipient_email = (request.get_json() or {}).get('email')

    try:
        if not recipient_email:
            return jsonify({"status": "error", "message": "No parent email provided", "code": 400}), 400
        if not is_valid_email(recipient_email):
            return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400 
        student = g.user
        recipient = g.session.query(Parent).filter_by(email=recipient_email).first()
        if not recipient:
            return jsonify({"status": "error", "message": "Parent not found", "code": 404}), 404
        if g.session.query(parent_student_association).filter_by(parent_id=student.id, student_id=recipient.id).first() is not None:
            return jsonify({"status": "error", "message": "The user is already listed as a parent", "code": 400}), 400

        # Check if there is any existing request that is the exact same.
        existing_request = g.session.query(ConnectionRequest).filter_by(sender_id=student.id, recipient_id=recipient.id).first()
        if existing_request and existing_request.status == 'pending':
            return jsonify({"status": "error", "message": "Request is already pending", "code": 400}), 400

        new_request = ConnectionRequest(sender_id=student.id, recipient_id=recipient.id, type='child_to_parent')
        g.session.add(new_request)
        g.session.commit()

        return jsonify({"status": "success", "message": "Request sent successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500


@app.route('/api/students/family/requests/<int:request_id>', methods=['PATCH'])
@jwt_required()
@role_required("student")
def student_respond_to_parent_request(request_id):
    response = (request.get_json() or {}).get('response')

    try:
        if not response:
            return jsonify({"status": "error", "message": "No response provided", "code": 400}), 400 
        student = g.user
        connection_request = g.session.query(ConnectionRequest).filter_by(id=request_id, recipient_id=student.id).first()
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

            student.parents.append(parent)
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


@app.route('/api/parents/family/requests/<int:request_id>', methods=['PATCH'])
@jwt_required()
@role_required("parent")
def parent_respond_to_student_request(request_id):
    response = (request.get_json() or {}).get('response')
    try:
        if not response:
            return jsonify({"status": "error", "message": "No response provided", "code": 400}), 400 

        parent = g.user
        connection_request = g.session.query(ConnectionRequest)\
            .filter_by(id=request_id, recipient_id=parent.id).first()
        if not connection_request:
            return jsonify({"status": "error", "message": "Request not found", "code": 404}), 404
        if connection_request.type != 'child_to_parent':
            return jsonify({"status": "error", "message": "Request not a child-parent connection", "code": 404}), 404
        if connection_request.status != "pending":
            return jsonify({"status": "error", "message": "Request already processed.", "code": 404}), 404

        if response == 'accept':
            student = g.session.query(Student).filter_by(id=connection_request.sender_id).first()
            if not student:
                return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404
            parent.children.append(student)
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

##### CLASS MGMT ####

@app.route('/api/classes', methods=['POST'])
@jwt_required()
@role_required("teacher")
def create_class():
    class_name = (request.get_json() or {}).get('class_name')

    if not class_name:
        return jsonify({"status": "error", "message": "Missing class name", "code": 400}), 400
    if len(class_name) > 60:
            return jsonify({"status": "error", "message": "Class name too long", "code": 400}), 400
    
    try:
        teacher = g.user
        if not teacher:
            return jsonify({"status": "error", "message": "Teacher not found", "code": 404}), 404
        
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


@app.route('/api/classes/<int:class_id>', methods=['DELETE'])
@jwt_required()
@role_required("teacher")
def delete_class(class_id):
    try:
        # Find the class with the given id
        class_ = g.session.query(Class).filter_by(id=class_id).first()

        # If the class doesn't exist
        if not class_:
            return jsonify({"status": "error", "message": "Class not found", "code": 404}), 404

        # Delete the class
        g.session.delete(class_)
        g.session.commit()
        return jsonify({"status": "success", "message": "Class successfully deleted", "code": 200}), 200
    
    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "An error occurred while deleting the class", "code": 500}), 500

@app.route('/api/classes', methods=['GET'])
@jwt_required()
def get_classes():
    if g.role == "parent":
        return jsonify({"status":"error","message":"Access forbidden","code":403}), 403
    try:
        if g.role == "student":
            student = g.user
            if student is None:
                return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404
            classes = [{"id": _class.id, "name": _class.class_name} for _class in student.classes]
            return jsonify({"status": "success", "classes": classes, "code": 200}), 200
        
        if g.role == "teacher":
            teacher = g.user
            if teacher is None:
                return jsonify({"status": "error", "message": "Teacher not found", "code": 404}), 404

            classes = [{"id": _class.id, "name": _class.class_name} for _class in teacher.classes]
            return jsonify({"status": "success", "classes": classes, "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        return jsonify({"status": "error", "message": "An error occurred", "code": 500}), 500


@app.route('/api/classes/<int:class_id>/students', methods=['GET'])
@jwt_required()
@role_required("teacher")
def get_students(class_id):
    try:
        # Check if the logged in user is the teacher of the class
        teacher_class = g.session.query(Class).filter_by(id=class_id, teacher_id=g.user.id).first()
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


@app.route('/api/classes/<int:class_id>/students/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_profile(class_id, student_id):
    try:
        # If the current user is a teacher, they can view the profile of the student who is in their class
        if g.role == "teacher":
            # Find the class
            class_ = g.session.query(Class).filter_by(id=class_id, teacher_id=g.user.id).first()
            if not class_:
                return jsonify({"status": "error", "message": "Class not found", "code": 404}), 404

            # Get the student's profile
            student_profile = g.user.get_student_profile(session=g.session, student_id=student_id)
            if not student_profile:
                return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404

        # If the current user is a parent, they can view the profile of their children
        elif g.role == "parent":
            # Get the child's profile
            student_profile = g.user.get_child_profile(session=g.session, student_id=student_id)
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


@app.route('/api/classes/<int:class_id>/code', methods=['GET'])
@jwt_required()
def get_class_code(class_id):
    try:
        class_ = g.session.query(Class).filter_by(id=class_id).first()
        if g.role == "parent":
            return jsonify({"status": "error", "message": "Unauthorized: Forbidden", "code": 403}), 403
        elif g.role == "student":
            if not g.session.query(student_class_association).filter_by(student_id=g.user.id, class_id=class_.id).first() is not None:
                return jsonify({"status": "error", "message": "Unauthorized: Forbidden", "code": 403}), 403
        elif g.role == "teacher":
            teacher_class = g.session.query(Class).filter_by(id=class_id, teacher_id=g.user.id).first()
            if not teacher_class:
                return jsonify({"status": "error", "message": "Unauthorized", "code": 403}), 403
        
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


@app.route('/api/students/classes/<int:class_id>/requests', methods=['DELETE'])
@jwt_required()
@role_required("student")
def student_leave_class(class_id):
    try:
        class_ = g.session.query(Class).filter_by(id=class_id).first()
        if not class_ or g.user not in class_.students:
            return jsonify({"status": "error", "message": "Class not found or student not enrolled", "code": 404}), 404

        class_.students.remove(g.user)
        g.session.commit()

        return jsonify({"status": "success", "message": "Class left successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500

@app.route('/api/teachers/classes/<int:class_id>/requests/<int:student_id>', methods=['DELETE'])
@jwt_required()
@role_required("teacher")
def teacher_remove_student_from_class(class_id, student_id):
    try:
        class_ = g.session.query(Class).filter_by(id=class_id, teacher_id=g.user.id).first()
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


##### PARENT / STUDENT MGMT #####

@app.route('/api/me/students/<int:student_id>', methods=['DELETE'])
@jwt_required()
@role_required("parent")
def parent_remove_student(student_id):
    try:
        student = g.session.query(Student).filter_by(id=student_id).first()
        if not student or student not in g.user.children:
            return jsonify({"status": "error", "message": "Student not found or not connected to the current user", "code": 404}), 404

        g.user.children.remove(student)
        g.session.commit()

        return jsonify({"status": "success", "message": "Student removed successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500

@app.route('/api/me/parents/<int:parent_id>', methods=['DELETE'])
@jwt_required()
@role_required("student")
def student_remove_parent(parent_id):
    try:
        parent = g.session.query(Parent).filter_by(id=parent_id).first()
        if not parent or g.user not in parent.children:
            return jsonify({"status": "error", "message": "Parent not found or not connected to the student", "code": 404}), 404

        parent.children.remove(g.user)
        g.session.commit()

        return jsonify({"status": "success", "message": "Parent removed successfully", "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        g.session.rollback()
        return jsonify({"status": "error", "message": "Something went wrong", "code": 500}), 500

##### REGISTRATION #####

@app.route('/api/teachers', methods=['POST'])
def register_teacher():
    data = request.form

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    confirmPassword = data.get('confirmPassword')
    image_path = None  # Default value for image_path
    file = request.files.get('image')
    
    try:

        if not name or not email or not password or not confirmPassword:
            return jsonify({"status": "error", "message": "Missing required fields", "code": 400}), 400
        
        if confirmPassword != password: # Check if passwords match.
            return jsonify({"status": "error", "message": "Passwords do not match", "code": 400}), 400

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


@app.route('/api/teachers', methods=['PATCH'])
@jwt_required()
@role_required("teacher")
def update_teacher():
    data = request.form  # changed from request.json
    image = request.files['image'] if 'image' in request.files else None
    name = data.get('name')
    email = data.get('email')

    try:
        # If no fields to update were provided
        if not name and not email and image is None:
            return jsonify({"status": "error", "message": "No fields to update were provided", "code": 400}), 400
        
        if name and len(name) > 60:
            return jsonify({"status": "error", "message": "Name too long", "code": 400}), 400
        
        teacher = g.session.query(Teacher).filter_by(id=g.user.id).first()
        if not teacher:
            return jsonify({"status":"error","message":"Teacher not found","code":404}), 404

        # Find the teacher
        teacher = g.session.query(Teacher).filter_by(id=g.user.id).first()
        if not teacher:
            return jsonify({"status": "error", "message": "Teacher not found", "code": 404}), 404

        # If an email was provided, validate it
        if email:
            if not is_valid_email(email):
                return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

            if g.session.query(User).filter(User.email==email, User.id!=g.user.id).first():
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


@app.route('/api/parents', methods=['POST'])
def register_parent():
    data = request.form

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    confirmPassword = data.get('confirmPassword')
    image_path = None  # Default value for image_path
    file = request.files.get('image')
    
    try:
        if not name or not email or not password or not confirmPassword:
            return jsonify({"status": "error", "message": "Missing required fields", "code": 400}), 400
        
        if confirmPassword != password: # Check if passwords match.
            return jsonify({"status": "error", "message": "Passwords do not match", "code": 400}), 400

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


@app.route('/api/parents', methods=['PATCH'])
@jwt_required()
@role_required("parent")
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
        
        parent = g.session.query(Parent).filter_by(id=g.user.id).first()
        if not parent:
            return jsonify({"status": "error", "message": "Parent not found", "code": 404}), 404

       # If an email was provided, validate it
        if email:
            if not is_valid_email(email):
                return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

            if g.session.query(User).filter(User.email==email, User.id!=g.user.id).first():
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


@app.route('/api/parents/children', methods=['GET'])
@jwt_required()
@role_required("parent")
def get_children():
    try:
        parent = g.session.query(Parent).filter_by(id=g.user.id).first()
        if parent is None:
            return jsonify({"status": "error", "message": "Parent not found", "code": 404}), 404

        children = [{"id": child.id, "name": child.name} for child in parent.children]
        return jsonify({"status": "success", "children": children, "code": 200}), 200

    except SQLAlchemyError as e:
        app.logger.error(f"SQLAlchemyError: {e}")
        return jsonify({"status": "error", "message": "An error occurred", "code": 500}), 500


### Student Endpoints ###

@app.route('/api/students', methods=['POST'])
def register_student():
    data = request.form

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    confirmPassword = data.get('confirmPassword') # Added a confirmed password field.
    file = request.files.get('image')
    
    try:
        if not name or not email or not password or not confirmPassword or not file:
            print("1")
            return jsonify({"status": "error", "message": "Missing required fields", "code": 400}), 400
        
        if confirmPassword != password: # Check if passwords match.
            return jsonify({"status": "error", "message": "Passwords do not match", "code": 400}), 400
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


@app.route('/api/students', methods=['PATCH'])
@jwt_required()
@role_required("student")
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
        
        # Find the student
        student = g.session.query(Student).filter_by(id=g.user.id).first()
        if not student:
            return jsonify({"status": "error", "message": "Student not found", "code": 404}), 404

        # If an email was provided, validate it
        if email:
            if not is_valid_email(email):
                return jsonify({"status": "error", "message": "Invalid email format", "code": 400}), 400

            if g.session.query(User).filter(User.email==email, User.id!=g.user.id).first():
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

@app.route('/api/students/family/requests/', methods=['GET'])
@jwt_required()
@role_required("student")
def list_family_requests():
    status = request.args.get('status', 'pending')
    q = g.session.query(ConnectionRequest).filter_by(
        recipient_id=g.user.id, type='parent_to_child', status=status
    )
    def shape(r):
        p = g.session.get(Parent, r.sender_id)
        return {
            "request_id": r.id,
            "from_parent_id": p.id if p else None,
            "from_parent_name": p.name if p else None,
            "from_parent_email": p.email if p else None,
            "created_at": getattr(r, "created_at", None)
        }
    return jsonify({"status":"success","requests":[shape(r) for r in q.all()],"code":200}), 200


@app.route('/api/students/classes/requests', methods=['GET'])
@jwt_required()
@role_required("student")
def list_class_invites():
    status = request.args.get('status', 'pending')
    q = g.session.query(ConnectionRequest).filter_by(
        recipient_id=g.user.id, type='class_invitation', status=status
    )
    def shape(r):
        cls = g.session.get(Class, r.class_id)
        tname = None
        if cls:
            t = g.session.get(Teacher, cls.teacher_id)
            tname = t.name if t else None
        return {
            "request_id": r.id,
            "class_id": cls.id if cls else None,
            "class_name": cls.class_name if cls else None,
            "teacher_name": tname,
            "created_at": getattr(r, "created_at", None)
        }
    return jsonify({"status":"success","requests":[shape(r) for r in q.all()],"code":200}), 200


@app.route('/api/students/family', methods=['GET'])
@jwt_required()
@role_required("student")
def list_my_parents():
    try:
        student = g.user
        parents = [{"id": p.id, "name": p.name, "email": p.email} for p in student.parents]
        return jsonify({"status":"success","parents": parents, "code": 200}), 200
    except SQLAlchemyError as e:
        g.session.rollback()
        return jsonify({"status":"error","message":"An error occurred","code":500}), 500

@app.route('/api/parents/family/requests/incoming', methods=['GET'])
@jwt_required()
@role_required("parent")
def list_parent_incoming_family_requests():
    status = request.args.get('status', 'pending')
    q = g.session.query(ConnectionRequest).filter_by(
        recipient_id=g.user.id, type='child_to_parent', status=status
    )
    def shape(r):
        s = g.session.get(Student, r.sender_id)
        return {
            "request_id": r.id,
            "from_student_id": s.id if s else None,
            "from_student_name": s.name if s else None,
            "from_student_email": s.email if s else None,
            "created_at": getattr(r, "created_at", None),
        }
    return jsonify({"status":"success","requests":[shape(r) for r in q.all()],"code":200}), 200


@app.route('/api/parents/family/requests/outgoing', methods=['GET'])
@jwt_required()
@role_required("parent")
def list_parent_outgoing_family_requests():
    status = request.args.get('status', 'pending')  # allow pending/rejected/accepted
    q = g.session.query(ConnectionRequest).filter_by(
        sender_id=g.user.id, type='parent_to_child', status=status
    )
    def shape(r):
        s = g.session.get(Student, r.recipient_id)
        return {
            "request_id": r.id,
            "to_student_id": s.id if s else None,
            "to_student_name": s.name if s else None,
            "to_student_email": s.email if s else None,
            "status": r.status,
            "created_at": getattr(r, "created_at", None),
        }
    return jsonify({"status":"success","requests":[shape(r) for r in q.all()],"code":200}), 200


##### MAIN #####

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    app.run(debug=True)

from flask import Flask, request, jsonify
from DatabaseManager import DatabaseManager
import json

app = Flask(__name__)

@app.route('/initialize_database', methods=['POST'])
def initialize_database():
    with DatabaseManager() as db_manager:
        result = db_manager.initialize_database()
    if result["status"] == "success":
        response = jsonify({"status": result["status"], "message": result["message"]})
        response.status_code = 200
    elif result["status"] == "partial":
        response = jsonify({"status": result["status"], "message": result["message"], "errors": result["errors"]})
        response.status_code = 206
    else:
        response = jsonify({"status": result["status"], "message": result["message"], "errors": result["errors"]})
        response.status_code = result["code"]

    return response


@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.get_json()
    student_number = data['student_number']
    student_name = data['student_name']
    img_path = data['img_path']
    
    with DatabaseManager() as db_manager:
        result = db_manager.add_student(student_number, student_name, img_path)

    if result["status"] == "success":
        response = jsonify({"status": result["status"], "message": result["message"]})
        response.status_code = 200
    else:
        response = jsonify({"status": result["status"], "message": result["message"], "errors": result["errors"]})
        response.status_code = result["code"]

    return response


if __name__ == '__main__':
    app.run(debug=True)

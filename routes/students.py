from flask import Blueprint, jsonify, request
from student_models.student_auth_model import login_student, create_student, get_student_with_matric_no
from student_models.update import reset_password, verify_account, change_password
from student_models.course_model import (get_all_available_courses_for_student, get_student_results,
                                         get_student_cgpa, get_student_dashboard, register_course,
                                         remove_course, get_registered_courses)
from services.otp_service import generate_otp
from utils.authorization import logout
import logging
from utils.decorator import role_required
from flasgger import swag_from

logger = logging.getLogger(__name__)
student_bp = Blueprint("student", __name__)

@student_bp.route('/signup', methods=['POST'])
@swag_from({
    'tags': ['Student'],
    'description': 'Create a new student account.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'email': {'type': 'string'},
                'password': {'type': 'string'},
                'date_of_birth': {'type': 'string'},
                'matric_no': {'type': 'string'},
                'dept_name': {'type': 'string'},
                'level': {'type': 'string'},
                'admission_year': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        201: {'description': 'Account created successfully'},
        400: {'description': 'All field required'},
        409: {'description': 'Matric number already exists'}
    }
})
def sign_up():
    data = request.get_json()
    first_name = data.get("first_name").title()
    last_name = data.get("last_name").title()
    email = data.get("email")
    password = data.get("password")
    dob = data.get("date_of_birth")
    matric_no = data.get("matric_no")
    dept_name = data.get("dept_name").title()
    level = data.get("level")
    admission_year = data.get("admission_year")

    if not all([first_name, last_name, email, password, dob, matric_no, dept_name, level, admission_year]):
        return jsonify({
            "error": "all field required"
        }), 400

    existing_user = get_student_with_matric_no(matric_no)

    if existing_user:
        return jsonify({
            "error": "A user with the same matric number already exists"
        }), 409

    response, status = create_student(first_name, last_name, email, password,
                                      dob, matric_no, dept_name, level, admission_year)

    return jsonify(response), status

@student_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Student'],
    'description': 'Login as student.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'matric_no': {'type': 'string'},
                'password': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Login successful'},
        400: {'description': 'Missing credentials'},
        404: {'description': 'Invalid credentials'}
    }
})
def login():
    data = request.get_json()

    matric_no = data.get("matric_no")
    password = data.get("password")

    if not all([matric_no, password]):
        return jsonify({
            "error": "please provide matric no and password"
        }), 400

    response, status = login_student(matric_no, password)

    return jsonify(response), status

@student_bp.route('/get-otp', methods=['GET'])
@swag_from({
    'tags': ['Student'],
    'description': 'Generate OTP for email verification.',
    'parameters': [
        {'name': 'email', 'in': 'query', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'OTP sent'},
        401: {'description': 'Email required'}
    }
})
def get_otp():
    email = request.args.get("email")

    if not email:
        return jsonify({
            "error": "please check your email or create an account"
        }), 401
    response, status = generate_otp(email)

    return jsonify(response), status

@student_bp.route('/verify-account', methods=['POST'])
@swag_from({
    'tags': ['Student'],
    'description': 'Verify student account using OTP.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'email': {'type': 'string'},
                'otp': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Account verified'},
        401: {'description': 'Verification failed'}
    }
})
def verify():
    data = request.get_json()
    try:
        email = data.get("email")
        otp = data.get("otp")

        response, status = verify_account(email, otp)

        return jsonify(response), status
    except Exception as e:
        logger.error(e)
        return jsonify({
            "error": "something went wrong"
        }), 500

@student_bp.route('/reset-password', methods=['PATCH'])
@swag_from({
    'tags': ['Student'],
    'description': 'Reset student password using OTP.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'email': {'type': 'string'},
                'otp': {'type': 'string'},
                'password': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Password reset successful'},
        401: {'description': 'Verification failed'}
    }
})
def reset_pass():
    data = request.get_json()
    try:
        email = data.get("email")
        otp = data.get("otp")
        password = data.get("password")

        response, status = reset_password(email, password, otp)

        return jsonify(response), status
    except Exception as e:
        logger.error(e)
        return jsonify({
            "error": "something went wrong"
        }), 500

@student_bp.route('/dashboard/<path:matric_no>', methods=['GET'])
@role_required("student")
@swag_from({
    'tags': ['Student'],
    'description': 'Get student dashboard information.',
    'parameters': [
        {'name': 'matric_no', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Dashboard data'},
        404: {'description': 'Student not found'}
    }
})
def dashboard(role, matric_no):

    try:
        student = get_student_dashboard(matric_no)
        if not student:
            return jsonify({
                "error": "student not found"
            }), 404

        return jsonify({
            "matric_no": student["matric_no"],
            "name": f"{student['first_name']} {student['last_name']}",
            "email": student["email"],
            "date_of_birth": student["date_of_birth"],
            "level": student["level"],
            "admission_year": student["admission_year"],
            "department": student["department"],
            "cgpa": float(student["cgpa"]) if student["cgpa"] else None
        }), 200
    except Exception as e:
        logger.error(f"exception occurred: {e}, {type(e)}")
        return jsonify({
            "error": "Internal server error"
        }), 500

@student_bp.route('/available-courses/<path:matric_no>', methods=['GET'])
@role_required("student")
@swag_from({
    'tags': ['Student'],
    'description': 'Get all available courses for registration.',
    'parameters': [
        {'name': 'matric_no', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'semester', 'in': 'query', 'type': 'string', 'required': True},
        {'name': 'session', 'in': 'query', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Available courses'},
        401: {'description': 'Semester or session missing'}
    }
})
def available_courses(role, matric_no):
    try:
        semester = request.args.get("semester")
        session = request.args.get("session")

        if not semester or not session:
            return jsonify({
                "error": "semester or session missing"
            }), 401

        courses = get_all_available_courses_for_student(matric_no, semester, session)

        if not courses:
            return jsonify({
                "message": "no courses available for registration yet"
            }), 200

        return jsonify({
            "matric_no": matric_no,
            "available_courses": courses
        }), 200

    except Exception as e:
        logger.error(e)
        return jsonify({
            "error": "something went wrong"
        }), 500

@student_bp.route('/enroll-for-course/<path:matric_no>', methods=['POST'])
@role_required("student")
@swag_from({
    'tags': ['Student'],
    'description': 'Enroll for a course.',
    'parameters': [
        {'name': 'matric_no', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'code': {'type': 'string'},
                'semester': {'type': 'string'},
                'session': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        201: {'description': 'Course registered'},
        400: {'description': 'Missing fields'}
    }
})
def enroll_course(role, matric_no):
    data = request.get_json()

    try:
        code = data.get("code").upper()
        semester = data.get("semester")
        session = data.get("session")

        response, status = register_course(matric_no, code, semester, session)

        return jsonify(response), status
    except Exception as e:
        logger.error(e)
        return jsonify({
            "error": "something went wrong"
        }), 500

@student_bp.route('/view-registered-courses/<path:matric_no>', methods=['GET'])
@role_required("student")
@swag_from({
    'tags': ['Student'],
    'description': 'View all registered courses.',
    'parameters': [
        {'name': 'matric_no', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Registered courses'},
        404: {'description': 'No course registered yet'}
    }
})
def view_registered_courses(role, matric_no):
    try:
        courses = get_registered_courses(matric_no)

        if not courses:
            return jsonify({
                "error": "no course registered yet"
            }), 404

        return jsonify({
            "matric_no": matric_no,
            "courses": courses,
        }), 200
    except Exception as e:
        logger.error(e)
        return jsonify({
            "error": "something went wrong"
        }), 500

@student_bp.route('/remove-course/<path:matric_no>', methods=['DELETE'])
@role_required("student")
@swag_from({
    'tags': ['Student'],
    'description': 'Remove a registered course.',
    'parameters': [
        {'name': 'matric_no', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'code': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Course removed'},
        400: {'description': 'Course not registered by this student'}
    }
})
def delete_course(role, matric_no):
    data = request.get_json()
    try:
        code = data.get("code").upper()

        response, status = remove_course(matric_no, code)

        return jsonify(response), status
    except Exception as e:
        logger.error(e)
        return jsonify({
            "error": "something went wrong"
        }), 500

@student_bp.route('/view-results/<path:matric_no>', methods=['GET'])
@role_required("student")
@swag_from({
    'tags': ['Student'],
    'description': 'View all approved results and CGPA.',
    'parameters': [
        {'name': 'matric_no', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Results and CGPA'}
    }
})
def view_result(role, matric_no):
    try:
        results = get_student_results(matric_no)
        cgpa = get_student_cgpa(matric_no)
        print(matric_no)
        print(cgpa)
        print(results)

        return jsonify({
            "matric_no": matric_no,
            "cgpa": cgpa,
            "results": results
        }), 200

    except Exception as e:
        logger.error(e)
        return jsonify({
            "error": "something went wrong"
        }), 500

@student_bp.route('/logout', methods=['POST'])
@role_required("student")
@swag_from({
    'tags': ['Student'],
    'description': 'Logout student.',
    'responses': {
        200: {'description': 'Logout successful'},
        401: {'description': 'Token missing or invalid'}
    }
})
def logout_user(role):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token missing or invalid"}), 401

        token = auth_header.split(" ")[1]
        logout(token)

        return jsonify({"message": "logout successful"}), 200
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "something went wrong"}), 500

@student_bp.route("/change-password", methods=["PUT"])
@role_required("student")
@swag_from({
    'tags': ['Student'],
    'description': 'Change student password.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'old_password': {'type': 'string'},
                'new_password': {'type': 'string'},
                'matric': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Password changed'},
        400: {'description': 'Old and new password required'}
    }
})
def student_change_password(role):
    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    matric = data.get("matric")

    if not old_password or not new_password:
        return jsonify({"error": "Old and new password required"}), 400

    result = change_password(matric, old_password, new_password)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result), 200
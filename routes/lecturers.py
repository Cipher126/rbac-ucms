import logging
from flask import Blueprint, request, jsonify
from lecturer_models.lecturer_auth import create_lecturer, lecturer_login, get_lecturer_with_staff_id
from services.otp_service import generate_otp
from lecturer_models.update import verify_account, reset_password, change_password
from lecturer_models.course_action import get_lecturers_courses, get_students_in_course, lecturer_dashboard
from lecturer_models.results_action import update_student_results, upload_students_results, get_course_result_list, get_course_result_list_pending
from utils.decorator import role_required
from utils.authorization import logout
from flasgger import swag_from

logger = logging.getLogger(__name__)

lecturer_bp = Blueprint("lecturer", __name__)

@lecturer_bp.route('/signup', methods=['POST'])
@swag_from({
    'tags': ['Lecturer'],
    'description': 'Create a new lecturer account.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'email': {'type': 'string'},
                'password': {'type': 'string'},
                'date_of_birth': {'type': 'string'},
                'staff_id': {'type': 'string'},
                'dept_name': {'type': 'string'},
                'designation': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        201: {'description': 'Account created successfully'},
        400: {'description': 'All field required'},
        409: {'description': 'Staff ID already exists'}
    }
})
def signup():
    data = request.get_json()
    first_name = data.get("first_name").title()
    last_name = data.get("last_name").title()
    email = data.get("email")
    password = data.get("password")
    date_of_birth = data.get("date_of_birth")
    staff_id = data.get("staff_id")
    dept_name = data.get("dept_name").title()
    designation = data.get("designation").title()

    if not all([first_name, last_name, email, password, date_of_birth, staff_id, dept_name, designation]):
        return jsonify({
            "error": "all field required"
        }), 400

    existing_user = get_lecturer_with_staff_id(staff_id)

    if existing_user:
        return jsonify({
            "error": "A user with the same staff id already exists"
        }), 409

    response, status = create_lecturer(first_name, last_name, email, password, date_of_birth, staff_id, dept_name, designation)

    return jsonify(response), status

@lecturer_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Lecturer'],
    'description': 'Login as lecturer.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'staff_id': {'type': 'string'},
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
    staff_id = data.get("staff_id")
    password = data.get("password")

    if not all([staff_id, password]):
        return jsonify({
            "error": "please provide your ID and password"
        }), 400

    response, status = lecturer_login(staff_id, password)

    return jsonify(response), status

@lecturer_bp.route('/get-otp', methods=['GET'])
@swag_from({
    'tags': ['Lecturer'],
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

    if email:
        response, status = generate_otp(email)

        return jsonify(response), status

    return jsonify({
        "error": "please check your email or create an account"
    }), 401

@lecturer_bp.route('/verify-account', methods=['POST'])
@swag_from({
    'tags': ['Lecturer'],
    'description': 'Verify lecturer account using OTP.',
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

@lecturer_bp.route('/dashboard/<path:staff_id>', methods=['GET'])
@role_required("lecturer")
@swag_from({
    'tags': ['Lecturer'],
    'description': 'Get lecturer dashboard statistics.',
    'parameters': [
        {'name': 'staff_id', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Dashboard data'}
    }
})
def view_dashboard(role, staff_id):
    try:
        response, status = lecturer_dashboard(staff_id)

        return jsonify(response), status
    except Exception as e:
        logger.error(f"exception occurred at lecturer dashboard: {e}")
        return {
            "error": "something went wrong"
        }, 500

@lecturer_bp.route('/upload-student-result', methods=['POST'])
@role_required("lecturer")
@swag_from({
    'tags': ['Lecturer'],
    'description': 'Upload a student\'s result for a course.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'matric_no': {'type': 'string'},
                'course_code': {'type': 'string'},
                'semester': {'type': 'string'},
                'session': {'type': 'string'},
                'score': {'type': 'number'},
                'remark': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        201: {'description': 'Result uploaded'},
        400: {'description': 'Required field missing'}
    }
})
def upload_result(role):
    try:
        data = request.get_json()
        matric = data.get("matric_no")
        code = data.get("course_code").upper()
        semester = data.get("semester")
        session = data.get("session")
        score = data.get("score")
        remark = data.get("remark").title()

        if not all([matric, code, session, semester, score, remark]):
            return jsonify({
                "error": "required field missing"
            }), 400

        response, status = upload_students_results(matric, code, session, semester, score, remark)

        return jsonify(response), status
    except Exception as e:
        logger.error(f"exception occurred while uploading result: {e}")
        return {
            "error": "something went wrong"
        }, 500

@lecturer_bp.route('/edit-student-results', methods=['PATCH'])
@role_required("lecturer")
@swag_from({
    'tags': ['Lecturer'],
    'description': 'Edit a student\'s result for a course.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'matric_no': {'type': 'string'},
                'course_code': {'type': 'string'},
                'semester': {'type': 'string'},
                'session': {'type': 'string'},
                'score': {'type': 'number'},
                'remark': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Result updated'},
        400: {'description': 'Required field missing'}
    }
})
def edit_result(role):
    data = request.get_json()
    matric = data.get("matric_no")
    code = data.get("course_code")
    semester = data.get("semester").title()
    session = data.get("session")
    score = data.get("score")
    remark = data.get("remark").title()

    if not all([matric, code, session, semester, score, remark]):
        return jsonify({
            "error": "required field missing"
        }), 400

    response, status = update_student_results(score, remark, matric, code, session, semester)
    return jsonify(response), status

@lecturer_bp.route('/reset-password', methods=['PATCH'])
@swag_from({
    'tags': ['Lecturer'],
    'description': 'Reset lecturer password using OTP.',
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

@lecturer_bp.route('/change-password/<path:staff_id>', methods=['PATCH'])
@role_required("lecturer")
@swag_from({
    'tags': ['Lecturer'],
    'description': 'Change lecturer password.',
    'parameters': [
        {'name': 'staff_id', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'old_password': {'type': 'string'},
                'new_password': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Password changed'},
        400: {'description': 'Old and new password required'}
    }
})
def change_pass(role, staff_id):
    data = request.get_json()

    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "Old and new password required"}), 400

    response, status = change_password(staff_id, old_password, new_password)
    return jsonify(response), status

@lecturer_bp.route('/get-all-courses/<path:staff_id>', methods=['GET'])
@role_required("lecturer")
@swag_from({
    'tags': ['Lecturer'],
    'description': 'Get all courses assigned to a lecturer.',
    'parameters': [
        {'name': 'staff_id', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'All lecturer courses'}
    }
})
def view_course(role, staff_id):
    try:
        response = get_lecturers_courses(staff_id)

        return jsonify({
            "message": "all lecturer courses",
            "courses": response
        }), 200
    except Exception as e:
        logger.error(f"exception occurred in get courses: {e}", exc_info=True)
        return {
            "error": "something went wrong"
        }, 500

@lecturer_bp.route('/view-students-result/<path:staff_id>', methods=['GET'])
@role_required("lecturer")
@swag_from({
    'tags': ['Lecturer'],
    'description': 'View all approved results for a course.',
    'parameters': [
        {'name': 'staff_id', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'code', 'in': 'query', 'type': 'string', 'required': True},
        {'name': 'semester', 'in': 'query', 'type': 'string', 'required': True},
        {'name': 'session', 'in': 'query', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Results returned'}
    }
})
def view_results(role, staff_id):
    try:
        code = request.args.get("code").upper()
        semester = request.args.get("semester")
        session = request.args.get("session")
        response, status = get_course_result_list(code, semester, session)

        return jsonify(response), status
    except Exception as e:
        logger.error(f"error occurred: {e}", exc_info=True)
        return {
            "error": "something went wrong"
        },500

@lecturer_bp.route('/view-students-result-pending/<path:staff_id>', methods=['GET'])
@role_required("lecturer")
@swag_from({
    'tags': ['Lecturer'],
    'description': 'View all pending results for a course.',
    'parameters': [
        {'name': 'staff_id', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'code', 'in': 'query', 'type': 'string', 'required': True},
        {'name': 'semester', 'in': 'query', 'type': 'string', 'required': True},
        {'name': 'session', 'in': 'query', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Pending results returned'}
    }
})
def view_pending_results(role, staff_id):
    code = request.args.get("code").upper()
    semester = request.args.get("semester")
    session = request.args.get("session")
    response, status = get_course_result_list_pending(code, semester, session)

    return jsonify(response), status

@lecturer_bp.route('/view-course-students/<path:staff_id>', methods=['GET'])
@role_required("lecturer")
@swag_from({
    'tags': ['Lecturer'],
    'description': 'View all students enrolled in a lecturer\'s course.',
    'parameters': [
        {'name': 'staff_id', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'code', 'in': 'query', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Students returned'}
    }
})
def view_course_students(role, staff_id):
    try:
        course_code = request.args.get("code").upper()
        response, status = get_students_in_course(staff_id, course_code)

        return jsonify(response), status
    except Exception as e:
        logger.error(f"exception occurred while getting lecturer courses: {e}", exc_info=True)
        return {
            "error": "something went wrong"
        }, 500

@lecturer_bp.route('/logout', methods=['POST'])
@role_required("lecturer")
@swag_from({
    'tags': ['Lecturer'],
    'description': 'Logout lecturer.',
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
        logger.error(e, exc_info=True)
        return jsonify({"error": "something went wrong"}), 500
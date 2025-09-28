import logging
from flask import Blueprint, request, jsonify
from utils.decorator import role_required
from utils.authorization import logout
from services.otp_service import generate_otp
from admin_models.update import verify_account, reset_password, change_password, get_admin_dashboard
from admin_models.admin_auth import create_admin, admin_login, get_admin_with_id
from admin_models.admin_actions import reactivate_user, approve_result, delete_user, suspend_student, unsuspend_student
from admin_models.course_models import (create_courses, create_department, get_courses_by_semester,
                                        get_department_by_id, get_list_of_department, get_courses_by_department,
                                        get_list_of_department_filtered_by_faculty, get_courses_by_level,
                                        update_course, update_department, delete_course, enroll_department_students)
from flasgger import swag_from

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/signup', methods=['POST'])
@swag_from({
    'tags': ['Admin'],
    'description': 'Create a new admin account.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'email': {'type': 'string'},
                'password': {'type': 'string'},
                'date_of_birth': {'type': 'string'},
                'admin_id': {'type': 'string'},
                'office': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        201: {'description': 'Account created successfully'},
        400: {'description': 'All field required'},
        409: {'description': 'Admin ID already exists'}
    }
})
def signup():
    data = request.get_json()
    first_name = data.get("first_name").title()
    last_name = data.get("last_name").title()
    email = data.get("email")
    password = data.get("password")
    date_of_birth = data.get("date_of_birth")
    admin_id = data.get("admin_id")
    office = data.get("office").title()

    if not all([first_name, last_name, email, password, date_of_birth, admin_id, office]):
        return jsonify({
            "error": "all field required"
        }), 400

    existing_user = get_admin_with_id(admin_id)

    if existing_user:
        return jsonify({
            "error": "A user with the same admin id already exists"
        }), 409

    response, status = create_admin(first_name, last_name, email, password, date_of_birth, admin_id, office)

    return jsonify(response), status

@admin_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Admin'],
    'description': 'Login as admin.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'admin_id': {'type': 'string'},
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

    admin_id = data.get("admin_id")
    password = data.get("password")

    if not admin_id or not password:
        return {
            "error": "please provide admin ID and password"
        }, 400

    response, status = admin_login(admin_id, password)

    return jsonify(response), status

@admin_bp.route('/get-otp', methods=['GET'])
@swag_from({
    'tags': ['Admin'],
    'description': 'Generate OTP for email verification.',
    'parameters': [
        {'name': 'email', 'in': 'query', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'OTP sent'},
        401: {'description': 'Email required'}
    }
})
def gen_otp():
    email = request.args.get('email')

    if not email:
        return {
            "error": "please provide your email"
        }, 401

    response, status = generate_otp(email)

    return jsonify(response), status

@admin_bp.route('/verify-account', methods=['PATCH'])
@swag_from({
    'tags': ['Admin'],
    'description': 'Verify admin account using OTP.',
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

@admin_bp.route('/reset-password', methods=['PATCH'])
@swag_from({
    'tags': ['Admin'],
    'description': 'Reset admin password using OTP.',
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

@admin_bp.route('/change-password/<path:admin_id>', methods=['PUT'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Change admin password.',
    'parameters': [
        {'name': 'admin_id', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'old_password': {'type': 'string'},
                'new_password': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Password changed'},
        400: {'description': 'Missing fields'}
    }
})
def change_pass(role, admin_id):
    data = request.get_json()

    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "Old and new password required"}), 400

    response, status = change_password(admin_id, old_password, new_password)
    return jsonify(response), status

@admin_bp.route('/dashboard/<admin_id>', methods=['GET'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Get admin dashboard statistics.',
    'parameters': [
        {'name': 'admin_id', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Dashboard data'}
    }
})
def dash(role, admin_id):
    response, status = get_admin_dashboard(admin_id)

    return jsonify(response), status

@admin_bp.route('/add-course', methods=['POST'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Add a new course.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'title': {'type': 'string'},
                'course_code': {'type': 'string'},
                'dept_id': {'type': 'string'},
                'level': {'type': 'string'},
                'semester': {'type': 'string'},
                'unit': {'type': 'integer'},
                'lecturer_firstname': {'type': 'string'},
                'lecturer_lastname': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        201: {'description': 'Course created'},
        400: {'description': 'Missing fields'}
    }
})
def add_course(role):

    data = request.get_json()
    title = data.get("title").title()
    code = data.get("course_code").upper()
    dept_id = data.get("dept_id")
    level = data.get("level")
    semester = data.get("semester")
    unit = data.get("unit")
    lecturer_firstname = data.get("lecturer_firstname").title()
    lecturer_lastname = data.get("lecturer_lastname").title()

    if not all([title, code, dept_id, level, semester, unit, lecturer_firstname, lecturer_lastname]):
        return {
            "error": "all fields must be provided"
        }, 400


    response, status = create_courses(title, code, dept_id, level, semester, unit, lecturer_firstname, lecturer_lastname)

    return jsonify(response), status

@admin_bp.route('/add-department', methods=['POST'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Add a new department.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'name': {'type': 'string'},
                'faculty': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        201: {'description': 'Department created'},
        400: {'description': 'Missing fields'}
    }
})
def add_dept(role):

    data = request.get_json()
    name = data.get('name').title()
    faculty = data.get("faculty").title()

    if not all([name, faculty]):
        return {
            "error": "all fields required"
        }, 400

    response, status = create_department(name, faculty)

    return jsonify(response), status

@admin_bp.route('/enroll-students-for-course-reg', methods=['POST'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Enroll students for course registration.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'dept_id': {'type': 'string'},
                'level': {'type': 'string'},
                'semester': {'type': 'string'},
                'session': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        201: {'description': 'Enrollment successful'},
        400: {'description': 'Missing fields'}
    }
})
def enroll(role):
    data = request.get_json()
    dept_id = data.get("dept_id")
    level = data.get("level")
    semester = data.get("semester")
    session = data.get("session")

    if not all([dept_id, level, semester, session]):
        return {
            "error": "all field required"
        }, 400

    response, status = enroll_department_students(dept_id, level, semester, session)

    return jsonify(response), status

@admin_bp.route('/approve-result', methods=['PUT'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Approve results for a course.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'code': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Result approved'},
        500: {'description': 'Internal server error'}
    }
})
def approve(role):
    try:
        data = request.get_json()
        code = data.get("code").upper()

        response, status = approve_result(code)

        return jsonify(response), status
    except Exception as e:
        logger.error(f"error occurred while approving result: {e}")
        return {
            "error": "something went wrong"
        }, 500

@admin_bp.route('/suspend-student', methods=['PUT'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Suspend a student.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'matric_no': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Student suspended'}
    }
})
def suspend(role):

    data = request.get_json()

    matric_no = data.get("matric_no")

    response, status = suspend_student(matric_no)

    return jsonify(response), status

@admin_bp.route('/deactivate-user-account', methods=['PUT'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Deactivate a user account.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'user_id': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'User deactivated'}
    }
})
def delete_user_route(role):

    data = request.get_json()

    user_id = data.get("user_id")
    response, status = delete_user(user_id)

    return jsonify(response), status

@admin_bp.route('/unsuspend-student', methods=['PUT'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Unsuspend a student.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'matric_no': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Student unsuspended'}
    }
})
def un_sus(role):
    data = request.get_json()

    matric_no = data.get("matric_no")

    response, status = unsuspend_student(matric_no)

    return jsonify(response), status

@admin_bp.route('/reactivate-user-account', methods=['PUT'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Reactivate a user account.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'user_id': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'User reactivated'}
    }
})
def react(role):
    data = request.get_json()

    user_id = data.get("user_id")

    response, status = reactivate_user(user_id)

    return jsonify(response), status

@admin_bp.route('/delete-course', methods=['DELETE'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Delete a course.',
    'parameters': [
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'code': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Course deleted'},
        500: {'description': 'Internal server error'}
    }
})
def delete_course_route(role):
    try:
        data = request.get_json()

        code = data.get("code").upper()

        response, status = delete_course(code)

        return jsonify(response), status

    except Exception as e:
        logger.error(f"exception occurred: {e}")
        return {
            "error": "something went wrong"
        }, 500

@admin_bp.route('/get-course-by-level', methods=['GET'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Get courses by level.',
    'parameters': [
        {'name': 'level', 'in': 'query', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Courses by level'}
    }
})
def get_course_level(role):

    level = request.args.get("level")

    response, status = get_courses_by_level(level)

    return jsonify(response), status

@admin_bp.route('/get-course-department', methods=['GET'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Get courses by department.',
    'parameters': [
        {'name': 'dept_id', 'in': 'query', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Courses by department'}
    }
})
def get_dept_course(role):

    dept_id = request.args.get("dept_id")

    response, status = get_courses_by_department(dept_id)

    return jsonify(response), status

@admin_bp.route('/edit-course/<course_code>', methods=['PUT'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Edit course details.',
    'parameters': [
        {'name': 'course_code', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'title': {'type': 'string'},
                'code': {'type': 'string'},
                'dept_id': {'type': 'string'},
                'level': {'type': 'string'},
                'semester': {'type': 'string'},
                'lecturer_id': {'type': 'string'},
                'unit': {'type': 'integer'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Course updated'},
        400: {'description': 'No valid fields to update'}
    }
})
def edit_course(role, course_code):
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided for update"}), 400

        allowed_fields = {"title", "code", "dept_id", "level", "semester", "lecturer_id", "unit"}
        update_fields = {k: v for k, v in data.items() if k in allowed_fields and v is not None}

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        result, status = update_course(course_code, update_fields)

        return jsonify(result), status

    except Exception as e:
        logger.error(f"Exception in edit_course: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@admin_bp.route('/edit-department/<dept_id>', methods=['PUT'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Edit department details.',
    'parameters': [
        {'name': 'dept_id', 'in': 'path', 'type': 'string', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {
            'properties': {
                'name': {'type': 'string'},
                'faculty': {'type': 'string'}
            }
        }}
    ],
    'responses': {
        200: {'description': 'Department updated'},
        400: {'description': 'No valid fields to update'}
    }
})
def edit_dept(role, dept_id):
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided for update"}), 400

        allowed_fields = {"name", "faculty"}
        update_fields = {k: v for k, v in data.items() if k in allowed_fields and v is not None}

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        result, status = update_department(dept_id, update_fields)

        return jsonify(result), status

    except Exception as e:
        logger.error(f"Exception in edit_course: {e}")
        return jsonify({"error": "Something went wrong"}), 500

@admin_bp.route('/get-all-departments', methods=['GET'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Get all departments.',
    'responses': {
        200: {'description': 'All departments'}
    }
})
def get_dept(role):

    response, status = get_list_of_department()

    return jsonify(response), status

@admin_bp.route('/get-department-filtered-by-faculty', methods=['GET'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Get departments filtered by faculty.',
    'parameters': [
        {'name': 'faculty', 'in': 'query', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Departments by faculty'}
    }
})
def get_filtered_dept(role):

    faculty = request.args.get("faculty").title()

    response, status = get_list_of_department_filtered_by_faculty(faculty)

    return jsonify(response), status

@admin_bp.route('/get-dept-info/<dept_id>', methods=['GET'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Get department info by ID.',
    'parameters': [
        {'name': 'dept_id', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Department info'}
    }
})
def dept_info(role, dept_id):

    response, status = get_department_by_id(dept_id)

    return jsonify(response), status

@admin_bp.route('/get-courses-by-semester', methods=['GET'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Get courses by semester.',
    'parameters': [
        {'name': 'semester', 'in': 'query', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Courses by semester'}
    }
})
def get_semester_course(role):

    semester = request.args.get("semester")

    response, status = get_courses_by_semester(semester)

    return jsonify(response), status

@admin_bp.route('/logout', methods=['POST'])
@role_required("admin")
@swag_from({
    'tags': ['Admin'],
    'description': 'Logout admin.',
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
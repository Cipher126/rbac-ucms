"""
Student authentication model for account creation, login, and retrieval.

Functions:
    get_dept_id(name): Retrieves department ID by department name.
    create_student(...): Creates a new student account.
    get_dept_name(dept_id): Retrieves department name by department ID.
    get_student_with_matric_no(matric_no): Retrieves student details by matric number.
    get_all_user_with_id(user_id): Retrieves user details by user ID.
    login_student(matric_no, password): Authenticates student and returns JWT.

Note:
    Any user_id argument is of type uuid.
"""

from database.connection import connection_uri
import psycopg2
import logging
from services.secure_password import hash_password, generate_id, verify_hash_password
from utils.authorization import generate_jwt

logger = logging.getLogger(__name__)

def get_dept_id(name):
    """
    Retrieves department ID by department name.

    Args:
        name (str): Department name.

    Returns:
        str or None: Department ID or None if not found.
    """
    connection = connection_uri
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT dept_id FROM departments WHERE name = %s
        """, (name, ))
        dept_id = cursor.fetchone()
    return dept_id[0] if dept_id else None

def create_student(
    first_name,
    last_name,
    email,
    password,
    date_of_birth,
    matric_no,
    dept_name,
    level,
    admission_year
):
    """
    Creates a new student account.

    Args:
        first_name (str): Student's first name.
        last_name (str): Student's last name.
        email (str): Student's email.
        password (str): Student's password.
        date_of_birth (str): Student's date of birth.
        matric_no (str): Student's matriculation number.
        dept_name (str): Department name.
        level (str): Level.
        admission_year (str): Admission year.

    Returns:
        tuple: Student details and HTTP status code.

    Note:
        Any user_id argument is of type uuid.
    """
    user_id = generate_id()
    hashed_pw = hash_password(password)
    dept_id = get_dept_id(dept_name)

    if not dept_id:
        raise ValueError(f"Department '{dept_name}' not found.")

    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (user_id, first_name, last_name, email, password, date_of_birth, role_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, first_name, last_name, email, hashed_pw, date_of_birth, "student"))

            cursor.execute("""
                INSERT INTO students(matric_no, user_id, dept_id, level, admission_year)
                VALUES (%s, %s, %s, %s, %s)
            """, (matric_no, user_id, dept_id, level, admission_year))

        connection.commit()

        return {
            "message": "Account created successfully",
            "user_id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "matric_no": matric_no,
            "level": level,
            "department": dept_name,
            "email": email
        }, 200

    except psycopg2.Error as e:
        logger.error(e)
        return {"error": "something went wrong"}, 400

def get_dept_name(dept_id):
    """
    Retrieves department name by department ID.

    Args:
        dept_id (str): Department ID.

    Returns:
        str or None: Department name or None if not found.
    """
    connection = connection_uri
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM departments WHERE dept_id = %s
        """, (dept_id, ))
        dept_name = cursor.fetchone()
    return dept_name[0] if dept_name else None

def get_student_with_matric_no(matric_no):
    """
    Retrieves student details by matric number.

    Args:
        matric_no (str): Student matriculation number.

    Returns:
        dict or None: Student details or None if not found.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM students WHERE matric_no = %s AND is_suspended = FALSE
            """, (matric_no,))

            student = cursor.fetchone()

        if student:
            return {
                "matric_no": student[0],
                "user_id": student[1],
                "dept_id": student[2],
                "level": student[3],
                "admission_year": student[5],
                "graduation_year": student[6]
            }

        return None
    except psycopg2.Error as e:
        logger.error(f"DB error in get_student_with_matric: {e}")
        return None

def get_all_user_with_id(user_id):
    """
    Retrieves user details by user ID.

    Args:
        user_id (str): User identifier (uuid).

    Returns:
        dict or None: User details or None if not found.

    Note:
        Any user_id argument is of type uuid.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT first_name, last_name, email, password, role_name, is_verified FROM users 
                WHERE user_id = %s AND is_active = TRUE
            """, (user_id, ))

            user = cursor.fetchone()

        if user:
            return {
                "first_name": user[0],
                "last_name": user[1],
                "email": user[2],
                "password": user[3],
                "role":user[4],
                "is_verified": user[5]
            }

        return None

    except Exception as e:
        logger.error(f"DB error in get_all_user_with_id: {e}")
        return None

def login_student(matric_no, password):
    """
    Authenticates student and returns JWT.

    Args:
        matric_no (str): Student matriculation number.
        password (str): Student password.

    Returns:
        tuple: Message, JWT token, and HTTP status code.

    Note:
        Any user_id argument is of type uuid.
    """
    try:
        student = get_student_with_matric_no(matric_no)
        if not student:
            return {"error": "Invalid matric number or password"}, 401

        user = get_all_user_with_id(student["user_id"])
        if not user:
            return {"error": "User not found"}, 404

        if not verify_hash_password(password, user["password"]):
            return {"error": "Invalid matric number or password"}, 401

        dept_name = get_dept_name(student["dept_id"])
        token = generate_jwt(student["user_id"], user["role"])

        return {
            "message": "Login successful",
            "token": token,
            "matric_no": student["matric_no"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "email": user["email"],
            "department": dept_name,
            "level": student["level"],
            "admission_year": student["admission_year"],
            "graduation_year": student["graduation_year"],
            "account_status": user["is_verified"]
        }, 200

    except Exception as e:
        logger.error(e)
        return {
            "error": "internal server error"
        }, 500

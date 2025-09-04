"""
Lecturer authentication module for account creation, login, and retrieval.

Functions:
    create_lecturer(...): Creates a new lecturer account.
        Note: Any user_id argument is of type uuid.
    get_lecturer_with_staff_id(staff_id): Retrieves lecturer details by staff ID.
        Note: Any user_id argument is of type uuid.
    lecturer_login(staff_id, password): Authenticates lecturer and returns JWT.
        Note: Any user_id argument is of type uuid.
"""
import logging
from services.secure_password import hash_password, generate_id, verify_hash_password
from utils.authorization import generate_jwt
from database.connection import connection_uri
from student_models.student_auth_model import get_dept_id, get_all_user_with_id

logger = logging.getLogger(__name__)

def create_lecturer(first_name, last_name, email, password, date_of_birth, staff_id, dept_name, designation):
    """
    Creates a new lecturer account.

    Args:
        first_name (str): Lecturer's first name.
        last_name (str): Lecturer's last name.
        email (str): Lecturer's email.
        password (str): Lecturer's password.
        date_of_birth (str): Lecturer's date of birth.
        staff_id (str): Lecturer's staff identifier.
        dept_name (str): Department name.
        designation (str): Lecturer's designation.

    Returns:
        tuple: Lecturer details and HTTP status code.

    Note:
        Any user_id argument is of type uuid.
    """
    connection = connection_uri

    user_id = generate_id()
    hash_pw = hash_password(password)
    dept_id = get_dept_id(dept_name)

    if not dept_id:
        raise ValueError(f"Department '{dept_name}' not found.")

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                   INSERT INTO users (user_id, first_name, last_name, email, password, date_of_birth, role_name)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
               """, (user_id, first_name, last_name, email, hash_pw, date_of_birth, "lecturer"))

            cursor.execute("""
                   INSERT INTO lecturers (staff_id, user_id, dept_id, designation) 
                   VALUES (%s, %s, %s, %s)
               """, (staff_id, user_id, dept_id, designation))

        connection.commit()

        return {
            "message": "Account created successfully",
            "staff_id": staff_id,
            "designation": designation,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "department": dept_name
        }, 201

    except Exception as e:
        logger.error(f"DB error: something went wrong in create lecturer{e}")
        return {
            "error": "something went wrong"
        }, 500

def get_lecturer_with_staff_id(staff_id):
    """
    Retrieves lecturer details by staff ID.

    Args:
        staff_id (str): Lecturer's staff identifier.

    Returns:
        dict or None: Lecturer details or None if not found.

    Note:
        Any user_id argument is of type uuid.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM lecturers WHERE staff_id = %s
            """, (staff_id, ))

            lecturer = cursor.fetchone()

        if lecturer:
            return {
                "staff_id": lecturer[0],
                "user_id": lecturer[1],
                "dept_id": lecturer[2],
                "designation": lecturer[3]
            }

        return None
    except Exception as e:
        logger.error(f" DB error in get_lecturer_with_staff_id, {e}")
        return None

def lecturer_login(staff_id, password):
    """
    Authenticates lecturer and returns JWT.

    Args:
        staff_id (str): Lecturer's staff identifier.
        password (str): Lecturer's password.

    Returns:
        tuple: Message, verification status, JWT token, and HTTP status code.

    Note:
        Any user_id argument is of type uuid.
    """
    try:
        lecturer = get_lecturer_with_staff_id(staff_id)
        if not lecturer:
            return {
                "error": "Invalid ID number or password"
            }, 404

        user = get_all_user_with_id(lecturer["user_id"])

        if not user:
            return {
                "error": "User not found"
            }, 404

        if not verify_hash_password(password ,user["password"]):
            return {
                "error": "Invalid ID number or password"
            }, 404

        token = generate_jwt(lecturer["user_id"], "lecturer")

        return {
            "message": f"welcome {lecturer['designation']}. {user['first_name']} {user['last_name']}",
            "verification_status": user["is_verified"],
            "token": token
        }, 200

    except Exception as e:
        logger.error(e)
        return {
            "error": "internal server error"
        }, 500

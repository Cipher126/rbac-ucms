"""
Admin authentication module for account creation, login, and retrieval.

Functions:
    create_admin(...): Creates a new admin account.
        Note: Any user_id argument is of type uuid.
    get_admin_with_id(admin_id): Retrieves admin details by admin ID.
        Note: Any user_id argument is of type uuid.
    Admin_login(admin_id, password): Authenticates admin and returns JWT.
        Note: Any user_id argument is of type uuid.
"""
from database.connection import connection_uri
from lecturer_models.lecturer_auth import logger
from services.secure_password import generate_id, hash_password, verify_hash_password
from student_models.student_auth_model import get_all_user_with_id
from utils.authorization import generate_jwt

def create_admin(first_name, last_name, email, password, date_of_birth, admin_id, office):
    """
    Creates a new admin account.

    Args:
        first_name (str): Admin's first name.
        last_name (str): Admin's last name.
        email (str): Admin's email.
        password (str): Admin's password.
        date_of_birth (str): Admin's date of birth.
        admin_id (str): Admin identifier.
        office (str): Admin's office.

    Returns:
        tuple: Admin details and HTTP status code.

    Note:
        Any user_id argument is of type uuid.
    """
    connection = connection_uri

    user_id = generate_id()
    hash_pw = hash_password(password)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                   INSERT INTO users (user_id, first_name, last_name, email, password, date_of_birth, role_name)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
               """, (user_id, first_name, last_name, email, hash_pw, date_of_birth, "admin"))

            cursor.execute("""
                   INSERT INTO admins (admin_id, user_id, office) 
                   VALUES (%s, %s, %s)
               """, (admin_id, user_id, office))

        connection.commit()

        return {
            "message": "Account created successfully",
            "admin_id": admin_id,
            "office": office,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        }, 201

    except Exception as e:
        logger.error(f"DB error: something went wrong in create lecturer{e}")
        return {
            "error": "something went wrong"
        }, 500

def get_admin_with_id(admin_id):
    """
    Retrieves admin details by admin ID.

    Args:
        admin_id (str): Admin identifier.

    Returns:
        dict or None: Admin details or None if not found.

    Note:
        Any user_id argument is of type uuid.
    """
    connection = connection_uri

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM admins WHERE admin_id = %s
        """, (admin_id, ))

        admin = cursor.fetchone()

    if admin:
        return {
            "user_id": admin[1],
            "admin_id": admin[0],
            "office": admin[2]
        }

    return None

def admin_login(admin_id, password):
    """
    Authenticates admin and returns JWT.

    Args:
        admin_id (str): Admin identifier.
        password (str): Admin password.

    Returns:
        tuple: Message, JWT token, and HTTP status code.

    """
    admin = get_admin_with_id(admin_id)

    if not admin:
        return {
                "error": "Invalid ID number or password"
            }, 404

    try:
        user = get_all_user_with_id(admin.get("user_id"))
        hash_pw = user.get("password")

        if not user:
            return {
                "error": "Invalid ID number or password"
            }, 404

        if not verify_hash_password(password, hash_pw):
            return {
                "error": "invalid password"
            }, 403

        token = generate_jwt(admin["user_id"], "admin")

        return {
            "message": f"welcome admin. {user['first_name']} {user['last_name']}",
            "token": token
        }, 200

    except Exception as e:
        logger.error(f"exception occurred at login admin: {e}")
        return {
            "error": "internal server error"
        }, 500

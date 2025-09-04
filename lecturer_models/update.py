"""
Lecturer update module for profile and password management.

Functions:
    verify_account(email, otp): Verifies a lecturer's account using OTP.
    change_password(staff_id, old_password, new_password): Changes lecturer password after verifying old password.
    reset_password(email, password, otp): Resets lecturer password after OTP verification.
    set_new_designation(staff_id, new_designation): Updates lecturer's designation.

Note:
    Any user_id argument is of type uuid.
"""
from database.connection import connection_uri
from .lecturer_auth import get_lecturer_with_staff_id, logger
from student_models.student_auth_model import get_all_user_with_id
from services.otp_service import verify_otp
from services.secure_password import hash_password, verify_hash_password

def verify_account(email, otp):
    """
    Verifies a lecturer's account using OTP.

    Args:
        email (str): Lecturer's email address.
        otp (str): One-time password for verification.

    Returns:
        tuple: Message and HTTP status code.
    """
    connection = connection_uri
    if verify_otp(email, otp):
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET is_verified = TRUE WHERE email = %s
            """, (email, ))

            connection.commit()
        return {
            "message": "account verification successful"
        }, 200

    return {
        "error": "verification unsuccessful, check your otp"
    }, 401

def change_password(staff_id, old_password, new_password):
    """
    Changes lecturer password after verifying old password.

    Args:
        staff_id (str): Lecturer's staff identifier.
        old_password (str): Old password.
        new_password (str): New password.

    Returns:
        tuple: Message and HTTP status code.

    Note:
        Any user_id argument is of type uuid.
    """
    try:
        lecturer = get_lecturer_with_staff_id(staff_id)
        if not lecturer:
            return {
                "error": "Lecturer not found"
            }, 404

        user = get_all_user_with_id(lecturer["user_id"])
        if not user:
            return {
                "error": "User not found"
            }, 404

        if not verify_hash_password(old_password, user["password"]):
            return {
                "error": "Old password is incorrect"
            }, 403

        hashed_pw = hash_password(new_password)

        connection = connection_uri
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET password = %s WHERE user_id = %s
            """, (hashed_pw, lecturer["user_id"]))

        connection.commit()

        return {
            "message": "Password updated successfully"
        }, 200

    except Exception as e:
        logger.error(f"Error in lecturer_reset_password_logged_in: {e}")
        return {
            "error": "Internal server error"
        }, 500

def reset_password(email, password, otp):
    """
    Resets lecturer password after OTP verification.

    Args:
        email (str): Lecturer's email address.
        password (str): New password.
        otp (str): One-time password for verification.

    Returns:
        tuple: Message and HTTP status code.
    """
    connection = connection_uri
    hashed_pw = hash_password(password)
    if verify_otp(email, otp):
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET password = %s WHERE email = %s
            """, (hashed_pw, email))
            connection.commit()
        return {
            "message": "password reset successful"
        }, 200

    return {
        "error": "verification unsuccessful, check your otp"
    }, 401

def set_new_designation(staff_id, new_designation):
    """
    Updates lecturer's designation.

    Args:
        staff_id (str): Lecturer's staff identifier.
        new_designation (str): New designation.

    Returns:
        tuple: Message and HTTP status code.
    """
    connection = connection_uri
    try:
        lecturer = get_lecturer_with_staff_id(staff_id)

        if not lecturer:
            return {
                "error": "lecturer not found check your staff ID and try again"
            }, 404

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE lecturers SET designation = %s WHERE staff_id = %s
            """, (new_designation, staff_id))

        connection.commit()

        return {
            "message": "congratulations on your new designation"
        }, 200
    except Exception as e:
        logger.error(f"error occur in set new designation: {e}")
        return {
            "error": "something went wrong"
        }, 500
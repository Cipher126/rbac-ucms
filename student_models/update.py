"""
Student update module for account verification and password management.

Functions:
    verify_account(email, otp): Verifies a student's account using OTP.
    reset_password(email, password, otp): Resets student password after OTP verification.
    change_password(matric_no, current_password, new_password): Changes student password after verifying current password.

Note:
    Any user_id argument is of type uuid.
"""

from database.connection import connection_uri
from services.secure_password import hash_password, verify_hash_password
from services.otp_service import verify_otp

def verify_account(email, otp):
    """
    Verifies a student's account using OTP.

    Args:
        email (str): Student's email address.
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

def reset_password(email, password, otp):
    """
    Resets student password after OTP verification.

    Args:
        email (str): Student's email address.
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

def change_password(matric_no, current_password, new_password):
    """
    Changes student password after verifying current password.

    Args:
        matric_no (str): Student matriculation number.
        current_password (str): Current password.
        new_password (str): New password.

    Returns:
        dict: Message or error.
    """
    connection = connection_uri

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT user_id FROM students WHERE matric_no = %s
        """, (matric_no,))
        student_row = cursor.fetchone()

        if not student_row:
            return {"error": "Student not found"}

        user_id = student_row[0]

        cursor.execute("""
            SELECT password FROM users WHERE user_id = %s
        """, (user_id,))
        user_row = cursor.fetchone()

        if not user_row:
            return {"error": "User record not found"}

        stored_password = user_row[0]

        if not verify_hash_password(current_password, stored_password):
            return {"error": "Current password is incorrect"}

        hashed_new_password = hash_password(new_password)

        cursor.execute("""
            UPDATE users
            SET password = %s
            WHERE user_id = %s
        """, (hashed_new_password, user_id))

        connection.commit()

    return {"message": "Password changed successfully"}

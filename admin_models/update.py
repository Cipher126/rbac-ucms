"""
Admin update module for account verification, password management, and dashboard retrieval.

Functions:
    verify_account(email, otp): Verifies an account using OTP.
    reset_password(email, password, otp): Resets password after OTP verification.
    change_password(admin_id, current_password, new_password): Changes admin password after verifying current password.
        Note: Any user_id argument is of type uuid.
    get_admin_dashboard(admin_id): Retrieves admin dashboard statistics.
        Note: Any user_id argument is of type uuid.
"""
from database.connection import connection_uri
from lecturer_models.lecturer_auth import logger
from services.secure_password import hash_password, verify_hash_password
from services.otp_service import verify_otp

def verify_account(email, otp):
    """
    Verifies an account using OTP.

    Args:
        email (str): Email address of the user.
        otp (str): One-time password for verification.

    Returns:
        tuple: A message and HTTP status code.
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
    Resets password after OTP verification.

    Args:
        email (str): Email address of the user.
        password (str): New password.
        otp (str): One-time password for verification.

    Returns:
        tuple: A message and HTTP status code.
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

def change_password(admin_id, current_password, new_password):
    """
    Changes admin password after verifying current password.

    Args:
        admin_id (str): Admin identifier.
        current_password (str): Current password.
        new_password (str): New password.

    Returns:
        tuple: A message and HTTP status code.

    Note:
        Any user_id argument is of type uuid.
    """
    connection = connection_uri

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT user_id FROM admins WHERE admin_id = %s
        """, (admin_id,))
        admin_row = cursor.fetchone()

        if not admin_row:
            return {"error": "Student not found"}

        user_id = admin_row[0]

        cursor.execute("""
            SELECT password FROM users WHERE user_id = %s
        """, (user_id,))
        user_row = cursor.fetchone()

        if not user_row:
            return {"error": "User record not found"}, 404

        stored_password = user_row[0]

        if not verify_hash_password(current_password, stored_password):
            return {"error": "Current password is incorrect"}, 403

        hashed_new_password = hash_password(new_password)

        cursor.execute("""
            UPDATE users
            SET password = %s
            WHERE user_id = %s
        """, (hashed_new_password, user_id))

        connection.commit()

    return {"message": "Password changed successfully"}, 201


def get_admin_dashboard(admin_id):
    """
    Retrieves admin dashboard statistics.

    Args:
        admin_id (str): Admin identifier.

    Returns:
        tuple: Dashboard data and HTTP status code.

    Note:
        Any user_id argument is of type uuid.
    """
    connection = connection_uri
    dashboard_data = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT admin_id, user_id, office FROM admins WHERE admin_id = %s", (admin_id,))
            admin_row = cursor.fetchone()
            if not admin_row:
                return {"error": "Admin not found"}, 404

            admin_id, user_id, office = admin_row

            cursor.execute("SELECT first_name, last_name, email, role_name, is_active FROM users WHERE user_id = %s", (user_id,))
            user_row = cursor.fetchone()

            if not user_row:
                return {"error": "Admin user details not found"}, 404

            first_name, last_name, email, role_name, is_active = user_row

            dashboard_data["admin"] = {
                "admin_id": admin_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "office": office,
                "role": role_name,
            }

            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
            active_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = FALSE")
            inactive_users = cursor.fetchone()[0]

            dashboard_data["users"] = {
                "total": total_users,
                "active": active_users,
                "inactive": inactive_users
            }

            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM students WHERE is_suspended = TRUE")
            suspended_students = cursor.fetchone()[0]

            dashboard_data["students"] = {
                "total": total_students,
                "suspended": suspended_students
            }

            cursor.execute("SELECT COUNT(*) FROM lecturers")
            total_lecturers = cursor.fetchone()[0]

            dashboard_data["lecturers"] = {
                "total": total_lecturers
            }

            cursor.execute("SELECT COUNT(*) FROM courses")
            total_courses = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM courses WHERE semester = 'Harmattan'")
            this_semester_courses = cursor.fetchone()[0]

            dashboard_data["courses"] = {
                "total": total_courses,
                "this_semester": this_semester_courses
            }

            cursor.execute("SELECT COUNT(*) FROM departments")
            total_departments = cursor.fetchone()[0]

            dashboard_data["departments"] = {
                "total": total_departments
            }

        return dashboard_data, 200

    except Exception as e:
        logger.error(f"Exception occurred in get_admin_dashboard: {e}")
        return {"error": "Something went wrong"}, 500
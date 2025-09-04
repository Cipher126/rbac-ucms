"""
Admin actions module for managing users, students, and results.

Functions:
    approve_result(course_code): Approves results for a given course.
    delete_user(user_id): Disables a user account.
    suspend_student(matric_no): Suspends a student by matriculation number.
    reactivate_user(user_id): Enables a previously disabled user account.
    unsuspend_student(matric_no): Unsuspends a student by matriculation number.
"""
from database.connection import connection_uri
from lecturer_models.lecturer_auth import logger
from student_models.course_model import get_course_id

def approve_result(course_code):
    """
    Approves the results for a specific course.

    Args:
        course_code (str): The code of the course to approve results for.

    Returns:
        tuple: A message and HTTP status code.
    """
    connection = connection_uri
    try:
        course_id = get_course_id(course_code)
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE results SET is_approved = TRUE WHERE course_id = %s
            """, (course_id, ))

        connection.commit()

        return {
            "message": "results approved successfully"
        }, 200

    except Exception as e:
        logger.error(f"exception happened while approving result: {e}")
        return {
            "error": "something went wrong"
        }, 500

def delete_user(user_id):
    """
    Disables a user account.

    Args:
        user_id (uuid): The ID of the user to disable.

    Returns:
        tuple: A message and HTTP status code.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET is_active = FALSE WHERE user_id = %s
            """, (user_id, ))
        connection.commit()

        return {
            "message":"user account has been disabled successfully"
        }, 200

    except Exception as e:
        logger.error(f"exception occurred at delete user: {e}")
        return {
            "error": "something went wrong"
        }, 500

def suspend_student(matric_no):
    """
    Suspends a student.

    Args:
        matric_no (str): The matriculation number of the student to suspend.

    Returns:
        tuple: A message and HTTP status code.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                    UPDATE students SET is_suspended = TRUE WHERE matric_no = %s
                """, (matric_no,))
        connection.commit()

        return {
            "message": "student has been suspended successfully"
        }, 200

    except Exception as e:
        logger.error(f"exception occurred at suspend student: {e}")
        return {
            "error": "something went wrong"
        }, 500

def reactivate_user(user_id):
    """
    Enables a previously disabled user account.

    Args:
        user_id (uuid): The ID of the user to enable.

    Returns:
        tuple: A message and HTTP status code.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE users SET is_active = TRUE WHERE user_id = %s
            """, (user_id, ))
        connection.commit()

        return {
            "message":"user account has been enabled successfully"
        }, 200

    except Exception as e:
        logger.error(f"exception occurred at reactivate user: {e}")
        return {
            "error": "something went wrong"
        }, 500

def unsuspend_student(matric_no):
    """
    Unsuspends a student.

    Args:
        matric_no (str): The matriculation number of the student to unsuspend.

    Returns:
        tuple: A message and HTTP status code.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                    UPDATE students SET is_suspended = FALSE WHERE matric_no = %s
                """, (matric_no,))
        connection.commit()

        return {
            "message": "student has been unsuspended successfully"
        }, 200

    except Exception as e:
        logger.error(f"exception occurred at unsuspend student: {e}")
        return {
            "error": "something went wrong"
        }, 500
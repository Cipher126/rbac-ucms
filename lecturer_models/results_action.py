"""
Lecturer results action module for managing student results.

Functions:
    upload_students_results(matric_no, code, session, semester, score, remark): Uploads a student's result for a course.
    update_student_results(score, remark, matric_no, code, session, semester): Updates a student's result for a course.
    get_course_result_list(course_code, semester, session): Retrieves all approved results for a course.
    get_course_result_list_pending(course_code, semester, session): Retrieves all pending results for a course.

Note:
    Any user_id argument is of type uuid.
"""
import psycopg2

from database.connection import connection_uri
from .lecturer_auth import logger
from student_models.course_model import get_course_id, update_student_cgpa


def upload_students_results(matric_no, code, session, semester, score, remark):
    """
    Uploads a student's result for a course.

    Args:
        matric_no (str): Student's matriculation number.
        code (str): Course code.
        session (str): Academic session.
        semester (str): Semester.
        score (float): Student's score.
        remark (str): Remark for the result.

    Returns:
        tuple: Message, grade, and HTTP status code.
    """
    connection = connection_uri
    course_id = get_course_id(code)

    if course_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO results (matric_no, course_id, session, semester, score, remark)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING grade;
                """, (matric_no, course_id, session, semester, score, remark))

                grade = cursor.fetchone()[0]
            connection.commit()
            update_student_cgpa(matric_no)

            return {
                "message": "Grade uploaded successfully",
                "course_code": code,
                "matric_no": matric_no,
                "grade": grade
            }, 200
        except psycopg2.errors.UniqueViolation:
            connection.rollback()
            return {
                "error": "Result for this student and course already exists"
            }, 400

        except Exception as e:
            logger.error(f"error occurred in upload_student_report {e}")
            return {
                "error": "something went wrong"
            }, 500

    return {
        "error": "Invalid course code"
    }, 404

def update_student_results(score, remark, matric_no, code, session, semester):
    """
    Updates a student's result for a course.

    Args:
        score (float): Student's score.
        remark (str): Remark for the result.
        matric_no (str): Student's matriculation number.
        code (str): Course code.
        session (str): Academic session.
        semester (str): Semester.

    Returns:
        tuple: Message, grade, and HTTP status code.
    """
    connection = connection_uri
    course_id = get_course_id(code)

    if not course_id:
        return {
            "error": "Invalid course code"
        }, 404

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE results 
                SET score = %s, remark = %s
                WHERE matric_no = %s AND course_id = %s AND session = %s AND semester = %s
                RETURNING grade;
            """, (score, remark, matric_no, course_id, session, semester))

            updated = cursor.fetchone()
            connection.commit()

            if not updated:
                return {
                    "error": "No matching record found for this student/course/session/semester"
                }, 404

            return {
                "message": "Student grade updated successfully",
                "matric_no": matric_no,
                "course_code": code,
                "grade": updated[0],
                "score": score,
                "remark": remark
            }, 200

    except Exception as e:
        logger.error(f"Error updating result: {e}")
        return {
            "error": "Something went wrong"
        }, 500

def get_course_result_list(course_code, semester, session):
    """
    Retrieves all approved results for a course.

    Args:
        course_code (str): Course code.
        semester (str): Semester.
        session (str): Academic session.

    Returns:
        tuple: List of results and HTTP status code.
    """
    connection = connection_uri
    course_id = get_course_id(course_code)

    if not course_id:
        return {
            "error": f"course {course_code} not found"
        }, 404

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT r.matric_no, r.score, r.grade, r.remark, r.created_at
                FROM results r
                WHERE r.course_id = %s AND r.semester = %s AND r.session = %s AND r.is_approved = TRUE
            """, (course_id, semester, session))

            rows = cursor.fetchall()

        if not rows:
            return {
                "course_code": course_code,
                "semester": semester,
                "session": session,
                "results": []
            }, 200

        result_list = [
            {
                "matric_no": r[0],
                "score": float(r[1]) if r[1] is not None else None,
                "grade": r[2],
                "remark": r[3],
                "uploaded_at": r[4].strftime("%Y-%m-%d %H:%M:%S")
            }
            for r in rows
        ]

        return {
            "course_code": course_code,
            "semester": semester,
            "session": session,
            "results": result_list
        }, 200

    except Exception as e:
        logger.error(f"error getting results for {course_code}: {e}")
        return {
            "error": "something went wrong while fetching results"
        }, 500

def get_course_result_list_pending(course_code, semester, session):
    """
    Retrieves all pending results for a course.

    Args:
        course_code (str): Course code.
        semester (str): Semester.
        session (str): Academic session.

    Returns:
        tuple: List of results and HTTP status code.
    """
    connection = connection_uri
    course_id = get_course_id(course_code)

    if not course_id:
        return {
            "error": f"course {course_code} not found"
        }, 404

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT r.matric_no, r.score, r.grade, r.remark, r.created_at
                FROM results r
                WHERE r.course_id = %s AND r.semester = %s AND r.session = %s AND r.is_approved = FALSE
            """, (course_id, semester, session))

            rows = cursor.fetchall()

        if not rows:
            return {
                "course_code": course_code,
                "semester": semester,
                "session": session,
                "results": []
            }, 200

        result_list = [
            {
                "matric_no": r[0],
                "score": float(r[1]) if r[1] is not None else None,
                "grade": r[2],
                "remark": r[3],
                "uploaded_at": r[4].strftime("%Y-%m-%d %H:%M:%S")
            }
            for r in rows
        ]

        return {
            "course_code": course_code,
            "semester": semester,
            "session": session,
            "results": result_list
        }, 200

    except Exception as e:
        logger.error(f"error getting results for {course_code}: {e}")
        return {
            "error": "something went wrong while fetching results"
        }, 500
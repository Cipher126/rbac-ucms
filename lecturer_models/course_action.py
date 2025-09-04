"""
Lecturer course action module for managing courses assigned to lecturers and student enrollment.

Functions:
    get_department_name(dept_id): Retrieves department name by department ID.
    get_student_info(matric_no): Retrieves student information by matriculation number.
    get_lecturers_courses(lecturer_id): Retrieves courses assigned to a lecturer.
    get_students_in_course(lecturer_id, course_code): Retrieves students enrolled in a lecturer's course.
    get_student_count_for_course(course_id): Returns number of students registered in a given course.
    lecturer_dashboard(lecturer_id): Returns dashboard statistics for a lecturer.

Note:
    Any user_id argument is of type uuid.
"""
from database.connection import connection_uri
from student_models.course_model import get_course_code
from .lecturer_auth import logger, get_lecturer_with_staff_id

def get_department_name(dept_id):
    """
    Retrieves department name by department ID.

    Args:
        dept_id (str): Department ID.

    Returns:
        str or None: Department name or None if not found.
    """
    connection = connection_uri
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM departments WHERE dept_id = %s", (dept_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_student_info(matric_no):
    """
    Retrieves student information by matriculation number.

    Args:
        matric_no (str): Student's matriculation number.

    Returns:
        dict or None: Student information or None if not found.

    Note:
        Any user_id argument is of type uuid.
    """
    connection = connection_uri
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT user_id FROM students WHERE matric_no = %s
        """, (matric_no,))
        student_result = cursor.fetchone()

        if not student_result:
            return None
        user_id = student_result[0]

        cursor.execute("""
            SELECT first_name, last_name, email
            FROM users WHERE user_id = %s
        """, (user_id,))
        user_result = cursor.fetchone()

        if user_result:
            first_name, last_name, email = user_result
            return {
                "matric_no": matric_no,
                "name": f"{first_name} {last_name}",
                "email": email
            }

        return None

def get_lecturers_courses(lecturer_id):
    """
    Retrieves courses assigned to a lecturer.

    Args:
        lecturer_id (str): Lecturer's staff identifier.

    Returns:
        list: List of courses assigned to the lecturer.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT course_id, title, unit, level, semester, dept_id
                FROM courses
                WHERE lecturer_id = %s
            """, (lecturer_id, ))

            courses = cursor.fetchall()

            courses_list = []
            for course_id, title, unit, level, semester, dept_id in courses:
                dept_name = get_department_name(dept_id)

                courses_list.append({
                    "code": get_course_code(course_id),
                    "title": title,
                    "unit": unit,
                    "department": dept_name,
                    "level": level,
                    "semester": semester,
                    "course_id": course_id
                })

            return courses_list

    except Exception as e:
        logger.error(f"Error fetching lecturer courses: {e}")
        return []

def get_students_in_course(lecturer_id, course_code):
    """
    Retrieves students enrolled in a lecturer's course.

    Args:
        lecturer_id (str): Lecturer's staff identifier.
        course_code (str): Course code.

    Returns:
        tuple: Dictionary with course code and list of students, and HTTP status code.
    """
    connection = connection_uri
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT course_id
                FROM courses
                WHERE lecturer_id = %s AND code = %s
            """, (lecturer_id, course_code))
            course = cursor.fetchone()

            if not course:
                return {
                    "error": "course not found for this lecturer"
                }, 404

            course_id = course[0]

            cursor.execute("""
                SELECT matric_no
                FROM enrollments
                WHERE course_id = %s
                ORDER BY matric_no
            """, (course_id,))
            matric_numbers = cursor.fetchall()

            students = []
            for (matric_no,) in matric_numbers:
                student_info = get_student_info(matric_no)
                if student_info:
                    students.append(student_info)

        return {
            "course_code": course_code,
            "students": students
        }, 200

    except Exception as e:
        logger.error(f"Error fetching students for course {course_code}: {e}", exc_info=True)
        return {
            "error": "something went wrong"
        }, 500

def get_student_count_for_course(course_id):
    """
    Returns number of students registered in a given course.

    Args:
        course_id (str): Course ID.

    Returns:
        int: Number of students registered.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM enrollments 
                WHERE course_id = %s
            """, (course_id, ))

            count = cursor.fetchone()
            return count[0] if count else 0

    except Exception as e:
        logger.error(f"Error fetching student count for {course_id}: {e}")
        return 0

def lecturer_dashboard(lecturer_id):
    """
    Returns dashboard statistics for a lecturer.

    Args:
        lecturer_id (str): Lecturer's staff identifier.

    Returns:
        tuple: Lecturer info, courses, stats, and HTTP status code.
    """
    try:
        lecturer_info = get_lecturer_with_staff_id(lecturer_id)

        courses = get_lecturers_courses(lecturer_id)
        course_list = []
        total_students = 0

        if courses:
            for c in courses:
                student_count = get_student_count_for_course(c["course_id"])
                total_students += student_count

                course_list.append({
                    "course_id": c["course_id"],
                    "code": c["code"],
                    "title": c["title"],
                    "unit": c["unit"],
                    "level": c["level"],
                    "semester": c["semester"],
                    "student_count": student_count
                })

        stats = {
            "total_courses": len(course_list),
            "total_students_taught": total_students
        }

        return {
            "lecturer_info": lecturer_info,
            "courses": course_list,
            "stats": stats
        }, 200

    except Exception as e:
        logger.error(f"Error building dashboard for {lecturer_id}: {e}")
        return {
            "error":"something went wrong"
        }, 500
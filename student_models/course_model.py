"""
Student course model module for managing course registration, retrieval, and CGPA calculation.

Functions:
    get_course_code(course_id): Retrieves course code by course ID.
    get_course_title(course_id): Retrieves course title by course ID.
    get_all_available_courses_for_student(matric_no, semester, session): Gets all available courses for a student for registration.
    get_course_id(course_code): Retrieves course ID by course code.
    register_course(matric_no, code, semester, session): Registers a course for a student.
    remove_course(matric_no, code): Removes a registered course for a student.
    get_registered_courses(matric_no): Retrieves all registered courses for a student.
    set_outstanding(matric_no): Sets outstanding courses for a student based on failed grades.
    update_student_cgpa(matric_no): Updates student's CGPA based on results.
    get_student_results(matric_no): Retrieves approved results for a student.
    get_student_cgpa(matric_no): Calculates and returns student's CGPA.
    get_student_dashboard(matric_no): Retrieves student dashboard information.

Note:
    Any user_id argument is of type uuid.
"""

from database.connection import connection_uri
from student_models.student_auth_model import logger


def get_course_code(course_id):
    """
    Retrieves course code by course ID.

    Args:
        course_id (str): Course identifier.

    Returns:
        str or None: Course code or None if not found.
    """
    connection = connection_uri
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT code FROM courses WHERE course_id = %s
        """, (course_id, ))

        course = cursor.fetchone()

    return course[0] if course else None

def get_course_title(course_id):
    """
    Retrieves course title by course ID.

    Args:
        course_id (str): Course identifier.

    Returns:
        str or None: Course title or None if not found.
    """
    connection = connection_uri

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT title FROM courses WHERE course_id = %s
        """, (course_id, ))

        course = cursor.fetchone()

    return course[0] if course else None

def get_all_available_courses_for_student(matric_no, semester, session):
    """
    Gets all available courses for a student for registration.

    Args:
        matric_no (str): Student matriculation number.
        semester (str): Semester.
        session (str): Academic session.

    Returns:
        list: List of available courses for registration.
    """
    connection = connection_uri
    with connection.cursor() as cursor:
        cursor.execute("""
                SELECT matric_no, course_id, semester, session 
                FROM enrollments 
                WHERE matric_no = %s AND semester = %s AND session = %s
            """, (matric_no, semester, session))

        courses = cursor.fetchall()

    available_courses = []

    for c in courses:
        course_code = get_course_code(c[1])
        title = get_course_title(c[1])
        available_courses.append({
            "matric_no": c[0],
            "course_code": course_code,
            "title": title,
            "semester": c[2],
            "session": c[3]
        })

    return available_courses

def get_course_id(course_code):
    """
    Retrieves course ID by course code.

    Args:
        course_code (str): Course code.

    Returns:
        str or None: Course ID or None if not found.
    """
    connection = connection_uri
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT course_id FROM courses WHERE code = %s
        """, (course_code, ))

        course = cursor.fetchone()

    return course[0] if course else None

def register_course(matric_no, code, semester, session):
    """
    Registers a course for a student.

    Args:
        matric_no (str): Student matriculation number.
        code (str): Course code.
        semester (str): Semester.
        session (str): Academic session.

    Returns:
        dict: Message and HTTP status code.
    """
    course_id = get_course_id(code)
    if not course_id:
        return {"error": "Course not found"}, 404

    connection = connection_uri
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM registered_courses
            WHERE matric_no = %s AND course_id = %s AND semester = %s AND session = %s
        """, (matric_no, course_id, semester, session))

        existing = cursor.fetchone()
        if existing:
            return {"error": "Course already registered"}, 400

        cursor.execute("""
            INSERT INTO registered_courses (matric_no, course_id, semester, session)
            VALUES (%s, %s, %s, %s)
        """, (matric_no, course_id, semester, session))

        connection.commit()

    return {"message": "Course registered successfully"}, 201

def remove_course(matric_no, code):
    """
    Removes a registered course for a student.

    Args:
        matric_no (str): Student matriculation number.
        code (str): Course code.

    Returns:
        dict: Message and HTTP status code.
    """
    connection = connection_uri

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT course_id FROM courses WHERE code = %s
        """, (code,))
        course = cursor.fetchone()

    if not course:
        return {"error": "Course not found"}, 404

    course_id = course[0]

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM registered_courses
            WHERE matric_no = %s AND course_id = %s
        """, (matric_no, course_id))
        registered = cursor.fetchone()

        if not registered:
            return {"error": "Course not registered by this student"}, 400

        cursor.execute("""
            DELETE FROM registered_courses
            WHERE matric_no = %s AND course_id = %s
        """, (matric_no, course_id))

        connection.commit()

    return {"message": "Course removed successfully"}, 200

def get_registered_courses(matric_no):
    """
    Retrieves all registered courses for a student.

    Args:
        matric_no (str): Student matriculation number.

    Returns:
        list: List of registered courses.
    """
    connection = connection_uri

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM registered_courses WHERE matric_no = %s
        """, (matric_no, ))

        course = cursor.fetchall()

    registered_course = []

    if course:
        for c in course:
            course_code = get_course_code(c[1])
            title = get_course_title(c[1])
            registered_course.append({
                "course code": course_code,
                "title": title,
                "semester": c[2],
                "session": c[3]
            })

    return registered_course

def set_outstanding(matric_no):
    """
    Sets outstanding courses for a student based on failed grades.

    Args:
        matric_no (str): Student matriculation number.

    Returns:
        None
    """
    connection = connection_uri
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT course_id, semester, session 
            FROM results 
            WHERE matric_no = %s AND grade = 'F'
        """, (matric_no,))
        failed_courses = cursor.fetchall()

        if failed_courses:
            for course_id, semester, session in failed_courses:
                cursor.execute("""
                    INSERT INTO outstanding_courses (matric_no, course_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (matric_no, course_id))

                cursor.execute("""
                    INSERT INTO enrollments (matric_no, course_id, semester, session)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (matric_no, course_id, semester, session))
    connection.commit()

def update_student_cgpa(matric_no):
    """
    Updates student's CGPA based on results.

    Args:
        matric_no (str): Student matriculation number.

    Returns:
        float or None: Updated CGPA or None if no results.
    """
    connection = connection_uri
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT course_id, grade
            FROM results
            WHERE matric_no = %s
        """, (matric_no,))
        rows = cursor.fetchall()

        if not rows:
            return None

        total_points = 0
        total_units = 0

        for course_id, grade in rows:
            cursor.execute("SELECT unit FROM courses WHERE course_id = %s", (course_id,))
            course = cursor.fetchone()
            if not course:
                continue
            unit = course[0]

            if grade == "A":
                grade_point = 5
            elif grade == "B":
                grade_point = 4
            elif grade == "C":
                grade_point = 3
            elif grade == "D":
                grade_point = 2
            elif grade == "E":
                grade_point = 1
            else:
                grade_point = 0

            total_points += grade_point * unit
            total_units += unit

        if total_units == 0:
            return None

        cgpa = round(total_points / total_units, 2)

        cursor.execute("""
            UPDATE students
            SET cgpa = %s
            WHERE matric_no = %s
        """, (cgpa, matric_no))
        connection.commit()

        return cgpa

def get_student_results(matric_no):
    """
    Retrieves approved results for a student.

    Args:
        matric_no (str): Student matriculation number.

    Returns:
        list or dict: List of results or error message.
    """
    connection = connection_uri
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT course_id, grade
                FROM results
                WHERE matric_no = %s AND is_approved = TRUE
            """, (matric_no,))
            results = cursor.fetchall()
            print(results)

            result_list = []

            for course_id, grade in results:
                cursor.execute("SELECT code, title, unit FROM courses WHERE course_id = %s", (course_id,))
                course = cursor.fetchone()
                print(course)
                if not course:
                    continue

                course_code, course_title, unit = course

                if grade == "A":
                    grade_point = 5
                elif grade == "B":
                    grade_point = 4
                elif grade == "C":
                    grade_point = 3
                elif grade == "D":
                    grade_point = 2
                elif grade == "E":
                    grade_point = 1
                else:
                    grade_point = 0

                total_points = unit * grade_point

                result_list.append({
                    "course_code": course_code,
                    "course_title": course_title,
                    "unit": unit,
                    "grade": grade,
                    "grade_point": grade_point,
                    "total_points": total_points
                })

            return result_list
    except Exception as e:
        logger.error(f"exception occurred in get students results: {e}")
        return {
            "error": "something went wrong"
        }

def get_student_cgpa(matric_no):
    """
    Calculates and returns student's CGPA.

    Args:
        matric_no (str): Student matriculation number.

    Returns:
        float or None: CGPA or None if no results.
    """
    connection = connection_uri
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT course_id, grade
            FROM results
            WHERE matric_no = %s AND is_approved = TRUE
        """, (matric_no,))
        rows = cursor.fetchall()

        if not rows:
            return None

        total_points = 0
        total_units = 0

        for course_id, grade in rows:
            cursor.execute("SELECT unit FROM courses WHERE course_id = %s", (course_id,))
            course = cursor.fetchone()
            if not course:
                continue
            unit = course[0]

            if grade == 'A':
                point = 5
            elif grade == 'B':
                point = 4
            elif grade == 'C':
                point = 3
            elif grade == 'D':
                point = 2
            elif grade == 'E':
                point = 1
            else:
                point = 0

            total_points += point * unit
            total_units += unit

        if total_units == 0:
            return None

        cgpa = round(total_points / total_units, 2)
        return cgpa

def get_student_dashboard(matric_no):
    """
    Retrieves student dashboard information.

    Args:
        matric_no (str): Student matriculation number.

    Returns:
        dict or None: Student dashboard data or None if not found.
    """
    connection = connection_uri
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT user_id, dept_id, matric_no, level, admission_year, cgpa
                FROM students
                WHERE matric_no = %s
            """, (matric_no,))
            student = cursor.fetchone()
            if not student:
                return None

            user_id, dept_id, matric_no, level, admission_year, cgpa = student

            cursor.execute("SELECT first_name, last_name, email, date_of_birth FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return None
            first_name, last_name, email, date_of_birth = user

            cursor.execute("SELECT name FROM departments WHERE dept_id = %s", (dept_id,))
            dept = cursor.fetchone()
            department = dept[0] if dept else None

            return {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "date_of_birth": date_of_birth,
                "matric_no": matric_no,
                "level": level,
                "admission_year": admission_year,
                "department": department,
                "cgpa": cgpa
            }

    except Exception as e:
        print(e)
        return None

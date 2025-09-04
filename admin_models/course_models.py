"""
Admin course models module for managing departments and courses.

Functions:
    create_department(name, faculty): Creates a new department.
    get_lecturer_id_by_name(first_name, last_name): Retrieves lecturer ID by name.
    create_courses(...): Creates new courses.
    enroll_department_students(...): Enrolls students in department courses.
    update_course(code, fields_to_edit): Updates course information.
    update_department(dept_id, fields_to_edit): Updates department information.
    get_list_of_department(): Retrieves all departments.
    get_list_of_department_filtered_by_faculty(faculty): Retrieves departments by faculty.
    get_department_by_id(dept_id): Retrieves department by ID.
    get_courses_by_department(dept_id): Retrieves courses by department.
    get_courses_with_filter(filter_by, filter_id): Retrieves courses with filter.
    get_courses_by_level(level): Retrieves courses by level.
    get_courses_by_semester(semester): Retrieves courses by semester.
    delete_course(course_code): Deletes a course.

Note:
    Any user_id argument is of type uuid.
"""
from database.connection import connection_uri
from lecturer_models.lecturer_auth import logger
from services.secure_password import generate_id
from student_models.course_model import get_course_id


def create_department(name, faculty):
    """
    Creates a new department.

    Args:
        name (str): Department name.
        faculty (str): Faculty name.

    Returns:
        tuple: Department details and HTTP status code.
    """
    dept_id = generate_id()
    connection = connection_uri
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO departments (dept_id, name, faculty)
                VALUES (%s, %s, %s)
                RETURNING dept_id, name, faculty;
            """, (dept_id, name, faculty))

            department = cursor.fetchone()
        connection.commit()

        return {
            "message": "new department created successfully",
            "department_details" :{
                "ID": department[0],
                "name": department[1],
                "faculty": department[2]
            }
        }, 201

    except Exception as e:
        logger.error(f"exception occurred in create department {e}")
        return {
            "error": "something went wrong"
        }, 500


def get_lecturer_id_by_name(first_name, last_name):
    """
    Retrieves lecturer ID by name.

    Args:
        first_name (str): Lecturer's first name.
        last_name (str): Lecturer's last name.

    Returns:
        str or None: Lecturer ID or None if not found.

    Note:
        Any user_id argument is of type uuid.
    """
    try:
        connection = connection_uri
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT user_id
                FROM users WHERE first_name = %s AND last_name = %s
            """, (first_name, last_name))

            result = cursor.fetchone()
            if result:
                cursor.execute("""
                    SELECT staff_id FROM lecturers WHERE user_id = %s
                """, (result[0], ))

                lecturer_id = cursor.fetchone()

                return lecturer_id[0]

            return None

    except Exception as e:
        logger.error(e)
        return None

def create_courses(title, code, dept_id, level, semester, unit, lecturer_first_name, lecturer_last_name):
    """
    Creates new courses.

    Args:
        title (str): Course title.
        code (str): Course code.
        dept_id (str): Department ID.
        level (str): Level.
        semester (str): Semester.
        unit (int): Course unit.
        lecturer_first_name (str): Lecturer's first name.
        lecturer_last_name (str): Lecturer's last name.

    Returns:
        tuple: Message and HTTP status code.
    """
    course_id = generate_id()
    lecturer_id = get_lecturer_id_by_name(lecturer_first_name, lecturer_last_name)
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO courses (course_id, title, code, dept_id, level, semester, lecturer_id, unit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (course_id, title, code, dept_id, level, semester, lecturer_id, unit))

        connection.commit()

        return {
            "message": "courses created successfully"
        }, 201

    except Exception as e:
        logger.error(f"exception occurred in create courses: {e}")
        return {
            "error": "something went wrong"
        }, 500

def enroll_department_students(dept_id, level, semester, session):
    """
    Enrolls students in department courses.

    Args:
        dept_id (str): Department ID.
        level (str): Level.
        semester (str): Semester.
        session (str): Session.

    Returns:
        tuple: Message and HTTP status code.
    """
    connection = connection_uri
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT matric_no FROM students
                WHERE dept_id = %s AND level = %s
            """, (dept_id, level))
            students = cursor.fetchall()

            cursor.execute("""
                SELECT course_id FROM courses
                WHERE dept_id = %s AND level = %s AND semester = %s
            """, (dept_id, level, semester))
            courses = cursor.fetchall()

            for (matric_no,) in students:
                for (course_id,) in courses:
                    cursor.execute("""
                        INSERT INTO enrollments (matric_no, course_id, semester, session)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (matric_no, course_id, semester, session))

        connection.commit()

        return {
            "message": "course enrollment update successful, "
                       "student can now go ahead to do course registration"
        }, 201

    except Exception as e:
        logger.error(f"exception occurred in enroll department students: {e}")
        return {
            "error": "something went wrong"
        }, 500

def update_course(code, fields_to_edit):
    """
    Updates course information.

    Args:
        code (str): Course code.
        fields_to_edit (dict): Fields to update.

    Returns:
        tuple: Message and HTTP status code.
    """
    connection = connection_uri

    try:
        course_id = get_course_id(code)
        if not course_id:
            return {
                "error": "course with the entered course code does not exist"
            }, 404

        if not fields_to_edit:
            return {"error": "No fields provided to update"}, 400

        set_clause = ", ".join(f"{key} = %s" for key in fields_to_edit)
        values = list(fields_to_edit.values())

        values.extend([course_id])

        with connection.cursor() as cursor:
            cursor.execute(f""" UPDATE courses SET {set_clause} WHERE course_id = %s
            """, values)

        connection.commit()

        return {
            "message": "course information updated successfully"
        }, 200

    except Exception as e:
        logger.error(f"exception occurred at update course {e}")
        return {
            "error": "something went wrong"
        }, 500

def update_department(dept_id, fields_to_edit):
    """
    Updates department information.

    Args:
        dept_id (str): Department ID.
        fields_to_edit (dict): Fields to update.

    Returns:
        tuple: Message and HTTP status code.
    """
    connection = connection_uri

    try:
        if not fields_to_edit:
            return {"error": "No fields provided to update"}, 400
        set_clause = ", ".join(f"{key} = %s" for key in fields_to_edit)
        values = list(fields_to_edit.values())

        values.extend([dept_id])

        with connection.cursor() as cursor:
            cursor.execute(f""" UPDATE departments SET {set_clause} WHERE dept_id = %s
            """, values)

        connection.commit()

        return {
            "message": "department information updated successfully"
        }, 200

    except Exception as e:
        logger.error(f"exception occurred at update department {e}")
        return {
            "error": "something went wrong"
        }, 500

def get_list_of_department():
    """
    Retrieves all departments.

    Returns:
        tuple: List of departments and HTTP status code.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM departments 
            """)

            departments = cursor.fetchall()
        departments_list = []

        if departments:
            for d in departments:
                departments_list.append({
                    "dept_id": d[0],
                    "name": d[1],
                    "faculty": d[2]
                })

            count = len(departments_list)

            return {
                "message": "department fetched successfully",
                "total number of departments": count,
                "departments": departments_list
            }, 200
        count = len(departments_list)

        return {
            "total number of departments": count,
            "departments": departments_list
        }, 200

    except Exception as e:
        logger.error(f"exception occurred at get list of departments: {e}")
        return {
            "error": "something went wrong"
        }, 500


def get_list_of_department_filtered_by_faculty(faculty):
    """
    Retrieves departments by faculty.

    Args:
        faculty (str): Faculty name.

    Returns:
        tuple: List of departments and HTTP status code.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM departments WHERE faculty = %s
            """, (faculty, ))

            departments = cursor.fetchall()
        departments_list = []

        if departments:
            for d in departments:
                departments_list.append({
                    "dept_id": d[0],
                    "name": d[1],
                    "faculty": d[2]
                })

            count = len(departments_list)

            return {
                "message": f"Departments for faculty '{faculty}' fetched successfully",
                f"total number of departments in faculty of {faculty}": count,
                "departments": departments_list
            }, 200
        count = len(departments_list)

        return {
            f"total number of departments in {faculty}": count,
            "departments": departments_list
        }, 200

    except Exception as e:
        logger.error(f"exception occurred at get list of departments: {e}")
        return {
            "error": "something went wrong"
        }, 500

def get_department_by_id(dept_id):
    """
    Retrieves department by ID.

    Args:
        dept_id (str): Department ID.

    Returns:
        tuple: Department details and HTTP status code.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                    SELECT * FROM departments WHERE dept_id = %s
                """, (dept_id,))

            department = cursor.fetchone()

        if department:
            return {
                "message": "department returned successfully",
                "dept_id": department[0],
                "name": department[1],
                "faculty": department[2]
            }, 200

        return {
            "error": "department not found"
        }, 404

    except Exception as e:
        logger.error(f"exception occurred at get department by id: {e}")
        return {
            "error": "something went wrong"
        }, 500

def get_courses_by_department(dept_id):
    """
    Retrieves courses by department.

    Args:
        dept_id (str): Department ID.

    Returns:
        tuple: List of courses and HTTP status code.
    """
    connection = connection_uri

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name, faculty
                FROM departments
                WHERE dept_id = %s
            """, (dept_id,))
            dept = cursor.fetchone()

            if not dept:
                return {
                    "error": "department not found for the given ID"
                }, 404

            department_name, faculty = dept

            cursor.execute("""
                SELECT course_id, title, code, unit, level, semester
                FROM courses
                WHERE dept_id = %s
            """, (dept_id,))
            courses = cursor.fetchall()

        courses_list = []
        if courses:
            for c in courses:
                courses_list.append({
                    "course_id": c[0],
                    "course_code": c[2],
                    "title": c[1],
                    "unit": c[3],
                    "level": c[4],
                    "semester": c[5],
                    "department": department_name,
                    "faculty": faculty
                })

            return {
                "message": "list of courses by department",
                "courses_count": len(courses_list),
                "courses": courses_list
            }, 200

        return {
            "error": "no courses found for the department ID entered"
        }, 404

    except Exception as e:
        logger.error(f"exception occurred at get_courses_by_department: {e}")
        return {
            "error": "something went wrong"
        }, 500


def get_courses_with_filter(filter_by, filter_id):
    """
    Retrieves courses with filter.

    Args:
        filter_by (str): Filter key.
        filter_id (str): Filter value.

    Returns:
        tuple: List of courses and HTTP status code.
    """
    connection = connection_uri

    try:
        allowed_filters = {"dept_id", "level", "semester", "lecturer_id"}
        if filter_by not in allowed_filters:
            return {"error": "invalid filter key"}, 400
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT * FROM courses WHERE {filter_by} = %s
            """, (filter_id, ))

            courses = cursor.fetchall()
        courses_list = []

        if courses:
            for c in courses:
                courses_list.append({
                    "course_id": c[0],
                    "course_code": c[2],
                    "title": c[1],
                    "dept_id": c[3],
                    "unit": c[7],
                    "level": c[4],
                    "semester": c[5],
                    "lecturer_id": c[6]
                })

            return {
                "message": f"courses have been filtered by {filter_by}",
                "courses_count": len(courses_list),
                "courses": courses_list
            }, 200

        return {
            "error": "incorrect filter or filter_id"
        }, 403

    except Exception as e:
        logger.error(f"exception occurred in filter courses: {e}")
        return {
            "error": "something went wrong"
        }

def get_courses_by_level(level):
    """
    Returns all courses for a specific level.

    Args:
        level (str): Level.

    Returns:
        tuple: List of courses and HTTP status code.
    """
    return get_courses_with_filter("level", level)


def get_courses_by_semester(semester):
    """
    Returns all courses for a specific semester.

    Args:
        semester (str): Semester.

    Returns:
        tuple: List of courses and HTTP status code.
    """
    return get_courses_with_filter("semester", semester)

def delete_course(course_code):
    """
    Deletes a course.

    Args:
        course_code (str): Course code.

    Returns:
        tuple: Message and HTTP status code.
    """
    connection = connection_uri
    course_id = get_course_id(course_code)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM courses WHERE course_id = %s
            """, (course_id, ))

        connection.commit()

        return {
            "message": f"course with the following course code: {course_code} as been deleted"
        }, 200

    except Exception as e:
        logger.error(f"exception occurred at delete course: {e}")
        return {
            "error": "something went wrong"
        }
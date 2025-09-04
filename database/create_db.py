from connection import connection_uri

connection = connection_uri

with connection.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(36) PRIMARY KEY NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password TEXT NOT NULL,
            date_of_birth DATE NOT NULL,
            role_name VARCHAR(20) CHECK (role_name IN ('student', 'lecturer', 'admin')) NOT NULL,
            is_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)
    connection.commit()

with connection.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            dept_id VARCHAR(20) PRIMARY KEY NOT NULL,
            name VARCHAR(100) NOT NULL UNIQUE,
            faculty VARCHAR(100) NOT NULL
        )
    """)
    connection.commit()

with connection.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            matric_no VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            dept_id VARCHAR(20) NOT NULL REFERENCES departments(dept_id) ON DELETE CASCADE,
            level INT DEFAULT 100,
            cgpa NUMERIC(3,2) DEFAULT 0.00 CHECK (cgpa >= 0.00 AND cgpa <= 5.00),
            admission_year INT NOT NULL,
            graduation_year INT,
            is_suspended BOOLEAN DEFAULT FALSE
        )
    """)
    connection.commit()

with connection.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lecturers (
            staff_id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            dept_id VARCHAR(20) NOT NULL REFERENCES departments(dept_id) ON DELETE CASCADE,
            designation VARCHAR(50)
        )
    """)
    connection.commit()

with connection.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id VARCHAR(50) PRIMARY KEY,
            user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            office VARCHAR(100)
        )
    """)
    connection.commit()

with connection.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id VARCHAR(20) PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            code VARCHAR(20) UNIQUE NOT NULL,
            dept_id VARCHAR(20) NOT NULL REFERENCES departments(dept_id) ON DELETE CASCADE,
            level INT NOT NULL,
            semester VARCHAR(20) CHECK (semester IN ('Harmattan', 'Rain')),
            lecturer_id VARCHAR(50) REFERENCES lecturers(staff_id) ON DELETE CASCADE,
            unit INT CHECK (unit > 0)
        )
    """)
    connection.commit()

with connection.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            matric_no VARCHAR(50) REFERENCES students(matric_no) ON DELETE CASCADE,
            course_id VARCHAR(20) NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
            semester VARCHAR(20) CHECK (semester IN ('first', 'second', 'harmattan', 'rain')),
            session VARCHAR(9) CHECK (session ~ '^[0-9]{4}/[0-9]{4}$'),
            PRIMARY KEY (matric_no, course_id, semester, session)
        )
    """)
    connection.commit()

with connection.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS outstanding_courses (
            matric_no VARCHAR(50) REFERENCES students(matric_no) ON DELETE CASCADE,
            course_id VARCHAR(20) NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
            PRIMARY KEY (matric_no, course_id)
        )
    """)
    connection.commit()

with connection.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registered_courses (
            matric_no VARCHAR(50) REFERENCES students(matric_no) ON DELETE CASCADE,
            course_id VARCHAR(20) NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
            semester VARCHAR(20) CHECK (semester IN ('first', 'second', 'harmattan', 'rain')),
            session VARCHAR(9) CHECK (session ~ '^[0-9]{4}/[0-9]{4}$'),
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (matric_no, course_id, session, semester)
        )
    """)
    connection.commit()

with connection.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            matric_no VARCHAR(50) REFERENCES students(matric_no) ON DELETE CASCADE,
            course_id VARCHAR(50) REFERENCES courses(course_id) ON DELETE CASCADE,
            session VARCHAR(9) CHECK (session ~ '^[0-9]{4}/[0-9]{4}$'),
            semester VARCHAR(20) CHECK (semester IN ('first', 'second', 'harmattan', 'rain')),
            score NUMERIC(5,2),
            grade CHAR(1) GENERATED ALWAYS AS (
                CASE 
                    WHEN score >= 70 THEN 'A'
                    WHEN score >= 60 THEN 'B'
                    WHEN score >= 50 THEN 'C'
                    WHEN score >= 45 THEN 'D'
                    WHEN score >= 40 THEN 'E'
                    ELSE 'F'
                END
            ) STORED,
            remark VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_approved DEFAULT FALSE
            PRIMARY KEY (matric_no, course_id, session, semester)
        )
    """)
    connection.commit()

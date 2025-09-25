**RBAC University Course Management System (UCMS)**

A role-based access control (RBAC) Course Management System built with Flask, PostgreSQL, and Redis, designed to handle university operations such as student registration, lecturer assignment, course management, results approval, and administrative control.

This project demonstrates secure authentication (JWT), session handling, and error-handling middleware, making it a solid backend for a real-world academic management system.

**Features**

**Student**

  -  Register and login securely.
  -  View courses and enroll.
  -  Limited course management.
  -  Submit assignments.
  -  View results (once approved).
  -  Password change functionality.
  -  Dashboard.

**Lecturer**

  -  Dashboard.
  -  Assign grades/results.
  -  Edit student results.
  -  View courses assigned to them.
  -  View students taking their course(s).
  -  Password change functionalities.

**Admin**

  -  Create and update courses (assign lecturer at creation).
  -  Create and update departments.
  -  Create and update faculties.
  -  Password change functionalities.
  -  Approve results.
  -  Suspend/unsuspend students.
  -  Disable/reactivate users.
  -  Dashboard with system stats (users, students, lecturers, courses, departments).


**Tech Stack**

Backend: Flask (Python)

Database: PostgreSQL (psycopg2 for queries)

Authentication: JWT + Redis (session handling)

Password Security: bcrypt (hashing and verification)

Error Handling: Custom error middleware + logging


**Environment Variables**

Create a .env file in the root directory:

DATABASE_URL=postgresql://username:password@localhost:5432/ucms
JWT_SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379/0

▶️ Getting Started
1️⃣ **Clone the repository**
git clone https://github.com/your-username/rbac-ucms.git
cd rbac-ucms

2️⃣ **Create and activate virtual environment**
python -m venv .venv
source .venv/bin/activate   # On Linux/Mac
.venv\Scripts\activate      # On Windows

3️⃣ **Install dependencies**
pip install -r requirements.txt

4️⃣ **Run the application**
flask run

**Admin Dashboard Example Response**
{
  "admin": {
    "admin_id": "ADCI001",
    "name": "Registrar"
  },
  "users": {
    "total": 152,
    "active": 140,
    "inactive": 12
  },
  "students": {
    "total": 100,
    "suspended": 5
  },
  "lecturers": {
    "total": 30
  },
  "courses": {
    "total": 200,
    "this_semester": 95
  },
  "departments": {
    "total": 10
  }
}

**Sample API documentation**

| Endpoint                  | Method | Role    | Description                   |
| ------------------------- | ------ | ------- | ----------------------------- |
| `/admin/login`            | POST   | Admin   | Admin login                   |
| `/student/register`       | POST   | Student | Register a new student        |
| `/lecturer/assign-course` | POST   | Admin   | Assign a lecturer to a course |

**Future Improvements**

Implement real-time notifications with WebSockets.

Add CI/CD pipeline and Docker support.

Integration with payment APIs for school fees.

<img width="1054" height="642" alt="API4" src="https://github.com/user-attachments/assets/a109dfa6-d4b7-44bb-95a7-8925f6477c17" />
<img width="1030" height="641" alt="API3" src="https://github.com/user-attachments/assets/c3c92ad4-93a3-4623-90b2-ca40a0894afa" />
<img width="1163" height="644" alt="API2" src="https://github.com/user-attachments/assets/a07fedc8-438a-41c3-91f5-435e2a0974a9" />
<img width="1070" height="643" alt="API1" src="https://github.com/user-attachments/assets/5f45895d-cc44-4a28-ba10-73abe65c7b52" />

**License**

This project is licensed under the MIT License – free to use and modify.

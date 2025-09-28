![Python](https://img.shields.io/badge/python-3.10%2B-blue)  
![Flask](https://img.shields.io/badge/flask-2.x-green)  
![PostgreSQL](https://img.shields.io/badge/postgresql-15-blue)  
![License](https://img.shields.io/badge/license-MIT-yellow)


# RBAC-UCMS

**RBAC-UCMS (Role-Based Access Control – University Course Management System)** is a backend system built with **Flask**, **PostgreSQL**, and **Redis**.  
It provides secure and role-based access to manage university operations such as **student registration, lecturer assignment, course management, result approval, and administrative control**.

---

## Features

### Students
- Register and login securely (JWT authentication).
- View and enroll in courses.
- Submit assignments.
- View results (once approved).
- Update password.
- Access personal dashboard.

### Lecturers
- Dashboard for assigned courses.
- Manage student results (assign, edit, and approve).
- View students enrolled in their courses.
- Update password.

### Admins
- Dashboard with system statistics (students, lecturers, courses, departments).
- Create and update courses (assign lecturer at creation).
- Manage faculties and departments.
- Approve results.
- Suspend/unsuspend students.
- Disable/reactivate users.
- Update password.

---

## Tech Stack

- **Language:** Python (Flask framework)  
- **Database:** PostgreSQL (via `psycopg2`)  
- **Authentication:** JWT + Redis (session handling)  
- **Password Security:** bcrypt (hashing & verification) 

---

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL
- Redis
- pip (Python package manager)

### Installation

```bash

## Clone repository
git clone https://github.com/Cipher126/rbac-ucms.git
cd rbac-ucms

## Create virtual environment
python -m venv .venv
source .venv/bin/activate   # On Linux/Mac
.venv\Scripts\activate      # On Windows

## Install dependencies
pip install -r requirements.txt

```

## Configuration

```bash
Create a .env file in the project root and update with your environment variables:

DATABASE_URL=postgresql://username:password@localhost:5432/ucms
JWT_SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379/0

Ensure your PostgreSQL and Redis servers are running.
```

## Running the Application
flask run

## Usage

Students register/login and enroll in courses.  
Lecturers manage results for their assigned courses.  
Admins oversee users, courses, and departments.  
All actions are secured with **RBAC + JWT authentication**.  

### Example Admin Dashboard Response
```json
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

```


## API Documentation
Endpoints are RESTful and can be tested using **Postman** or any API client.  
(Swagger/OpenAPI docs can be added in future updates.)


## Contributing

Fork the repository.  

Create your feature branch:  
git checkout -b feature/new-feature  

Commit your changes:  
git commit -m "Add new feature"  

Push to your branch:  
git push origin feature/new-feature  

Open a Pull Request.


## License
This project is licensed under the **MIT License**.


## Contact
For questions or support, open an issue or contact [Cipher126](https://github.com/Cipher126).

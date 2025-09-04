"""
Main application entry point for the Course Management System.

This Flask app registers blueprints for students, admins, and lecturers,
providing API endpoints for each user type.

API documentation is available via Flasgger.
"""

from flask import Flask
from flasgger import Swagger
from routes.admin import admin_bp
from routes.students import student_bp
from routes.lecturers import lecturer_bp

app = Flask(__name__)
swagger = Swagger(app)

app.register_blueprint(student_bp, url_prefix='/api/students')
app.register_blueprint(admin_bp, url_prefix='/api/admins')
app.register_blueprint(lecturer_bp, url_prefix='/api/lecturers')

if __name__ == "__main__":
    app.run(debug=True)
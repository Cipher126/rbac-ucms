"""
Decorator utility module for role-based access control in Flask routes.

Functions:
    role_required(required_role): Decorator to restrict access to users with a specific role.

Note:
    Any user_id argument is of type uuid.
"""

from functools import wraps
from flask import request, jsonify

from student_models.student_auth_model import logger
from .authorization import verify_jwt


def role_required(required_role):
    """
    Decorator to restrict access to users with a specific role.

    Args:
        required_role (str): Required user role.

    Returns:
        function: Decorated function with role-based access control.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                header = request.headers.get("Authorization")
                if not header or not header.startswith("Bearer "):
                    return jsonify({"error": "Missing or Invalid token"}), 401

                token = header.split(" ")[1]
                payload = verify_jwt(token)

                if not payload:
                    return jsonify({"error": "Invalid or expired token"}), 401

                if payload.get("role") != required_role:
                    return jsonify({"error": "Access denied"}), 403

                return func(role=payload.get("role"), *args, **kwargs)
            except Exception as e:
                logger.error(f"exception occurred in decorator: {e}")
                return None

        return wrapper

    return decorator

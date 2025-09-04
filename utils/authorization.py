"""
Authorization utility module for JWT token generation, verification, and logout.

Functions:
    generate_jwt(user_id, role): Generates a JWT token for a user.
    verify_jwt(token): Verifies a JWT token and returns its payload.
    logout(token): Logs out a user by deleting their token from Redis.

Note:
    Any user_id argument is of type uuid.
"""

import jwt
import datetime
import os
from dotenv import load_dotenv
import redis

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_USER = os.getenv("REDIS_USER")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, username=REDIS_USER, password=REDIS_PASSWORD, decode_responses=True)

def generate_jwt(user_id, role):
    """
    Generates a JWT token for a user.

    Args:
        user_id (str): User identifier (uuid).
        role (str): User role.

    Returns:
        str: JWT token.
    """
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=2)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    token_str = token if isinstance(token, str) else token.decode()

    r.setex(token_str, 10800, user_id)

    return token_str

def verify_jwt(token):
    """
    Verifies a JWT token and returns its payload.

    Args:
        token (str): JWT token.

    Returns:
        dict or None: Payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")

        if r.get(token) == user_id:
            return payload
        else:
            return None

    except(jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def logout(token):
    """
    Logs out a user by deleting their token from Redis.

    Args:
        token (str): JWT token.

    Returns:
        None
    """
    r.delete(token)

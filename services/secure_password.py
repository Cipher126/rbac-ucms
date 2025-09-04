"""
Secure password service module for password hashing, verification, and ID generation.

Functions:
    hash_password(password): Hashes a password using bcrypt.
    verify_hash_password(password, hashed_password): Verifies a password against its hash.
    generate_id(): Generates a unique 8-character ID.

Note:
    Any user_id argument is of type uuid.
"""

import bcrypt
import uuid

def hash_password(password):
    """
    Hashes a password using bcrypt.

    Args:
        password (str): Plain text password.

    Returns:
        str: Hashed password.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_hash_password(password, hashed_password):
    """
    Verifies a password against its hash.

    Args:
        password (str): Plain text password.
        hashed_password (str): Hashed password.

    Returns:
        bool: True if password matches hash, False otherwise.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_id():
    """
    Generates a unique 8-character ID.

    Returns:
        str: Unique ID.
    """
    return str(uuid.uuid4()).replace("-", "")[:8]
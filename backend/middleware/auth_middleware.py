"""
Authentication Middleware
Handles dashboard authentication with JWT tokens
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from backend.config import config
import os


# Secret key for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")


class AuthMiddleware:
    """Authentication middleware for dashboard"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    @staticmethod
    def generate_token(username: str) -> str:
        """Generate JWT token"""
        payload = {
            "username": username,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    @staticmethod
    def verify_token(token: str) -> tuple[bool, str]:
        """
        Verify JWT token
        Returns: (valid, username or error_message)
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return True, payload["username"]
        except jwt.ExpiredSignatureError:
            return False, "Token expired"
        except jwt.InvalidTokenError:
            return False, "Invalid token"

    @staticmethod
    def authenticate(username: str, password: str) -> tuple[bool, str]:
        """
        Authenticate user credentials
        Returns: (success, token or error_message)
        """
        # Get credentials from config
        expected_username = config.get("security.dashboard_username", "admin")
        expected_password = config.get("security.dashboard_password", "macro")

        # Simple comparison (in production, use hashed passwords)
        if username == expected_username and password == expected_password:
            token = AuthMiddleware.generate_token(username)
            return True, token
        else:
            return False, "Invalid credentials"


def require_auth(f):
    """Decorator to require authentication for routes"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if authentication is required
        if not config.get("security.require_dashboard_auth", True):
            return f(*args, **kwargs)

        # Get token from header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "No authorization header"}), 401

        # Extract token
        try:
            token = auth_header.split(" ")[1]  # Bearer <token>
        except IndexError:
            return jsonify({"error": "Invalid authorization header"}), 401

        # Verify token
        valid, result = AuthMiddleware.verify_token(token)

        if not valid:
            return jsonify({"error": result}), 401

        # Add username to request context
        request.username = result

        return f(*args, **kwargs)

    return decorated_function

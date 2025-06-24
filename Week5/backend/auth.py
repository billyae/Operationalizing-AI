"""
Authentication module for the Bedrock Chatbot application.

This module provides JWT-based authentication, user management, and database operations
for user registration, login, and session management.

Author: AI Assistant
Date: 2024
"""

import jwt
import bcrypt
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# User database path
USERS_DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


def init_users_db():
    """
    Initialize the users database with required tables and default admin user.
    
    Creates the users table if it doesn't exist and adds a default admin user
    with username 'admin' and password 'admin123' for initial system access.
    
    Returns:
        None
    """
    conn = sqlite3.connect(USERS_DB_PATH)
    
    # Create users table with required fields
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Create default admin user (password: admin123) if not exists
    admin_exists = conn.execute(
        'SELECT COUNT(*) FROM users WHERE username = ?', 
        ('admin',)
    ).fetchone()[0]
    
    if admin_exists == 0:
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        conn.execute(
            'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
            ('admin', password_hash, 'admin@example.com')
        )
        conn.commit()
    
    conn.close()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with salt.
    
    Args:
        password (str): Plain text password to hash
        
    Returns:
        str: Hashed password with salt
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def verify_password(password: str, password_hash: bytes) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password (str): Plain text password to verify
        password_hash (bytes): Stored password hash
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)


def generate_token(user_id: int, username: str) -> str:
    """
    Generate a JWT token for authenticated user.
    
    Args:
        user_id (int): User's unique identifier
        username (str): User's username
        
    Returns:
        str: JWT token string
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token (str): JWT token to decode
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        Exception: If token is expired or invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


def authenticate_user(username: str, password: str) -> dict:
    """
    Authenticate user credentials and update last login time.
    
    Args:
        username (str): Username to authenticate
        password (str): Plain text password
        
    Returns:
        dict: User information if authentication successful, None otherwise
        Contains keys: id, username, email
    """
    conn = sqlite3.connect(USERS_DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Fetch user by username
    user = conn.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()
    
    # Verify password and update last login
    if user and verify_password(password, user['password_hash']):
        # Update last login timestamp
        conn.execute(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            (user['id'],)
        )
        conn.commit()
        conn.close()
        
        return {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }
    
    conn.close()
    return None


def create_user(username: str, password: str, email: str = None) -> bool:
    """
    Create a new user account.
    
    Args:
        username (str): Unique username for the new user
        password (str): Plain text password
        email (str, optional): User's email address
        
    Returns:
        bool: True if user created successfully, False if username exists
    """
    try:
        conn = sqlite3.connect(USERS_DB_PATH)
        password_hash = hash_password(password)
        
        conn.execute(
            'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
            (username, password_hash, email)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Username already exists
        return False


def require_auth(f):
    """
    Decorator to require authentication for API endpoints.
    
    This decorator validates JWT tokens from the Authorization header
    and adds user information to the request object.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function that requires valid JWT token
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        # Extract token from Authorization header (Bearer <token>)
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Format: "Bearer <token>"
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Decode token and add user info to request
            payload = decode_token(token)
            request.current_user = payload
        except Exception as e:
            return jsonify({'error': str(e)}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


# Initialize user database on module import
init_users_db() 
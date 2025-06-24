"""
Unit tests for authentication module.

This module tests user authentication, JWT token management, password hashing,
and database operations.
"""

import unittest
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock
import sys
import jwt
from datetime import datetime, timedelta

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from auth import (
    hash_password, verify_password, generate_token, decode_token,
    authenticate_user, create_user, require_auth, init_users_db,
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
)


class TestPasswordFunctions(unittest.TestCase):
    """Test password hashing and verification functions."""
    
    def test_hash_password(self):
        """Test password hashing functionality."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Check that hash is bytes and not empty
        self.assertIsInstance(hashed, bytes)
        self.assertGreater(len(hashed), 0)
        
        # Check that hash is different from original password
        self.assertNotEqual(hashed, password.encode())
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Verify correct password
        self.assertTrue(verify_password(password, hashed))
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password_456"
        hashed = hash_password(password)
        
        # Verify incorrect password
        self.assertFalse(verify_password(wrong_password, hashed))
    
    def test_hash_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)
        
        self.assertNotEqual(hash1, hash2)


class TestJWTFunctions(unittest.TestCase):
    """Test JWT token generation and verification functions."""
    
    def test_generate_token(self):
        """Test JWT token generation."""
        user_id = 123
        username = "testuser"
        
        token = generate_token(user_id, username)
        
        # Check that token is string and not empty
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
        
        # Decode token manually to verify contents
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        self.assertEqual(payload['user_id'], user_id)
        self.assertEqual(payload['username'], username)
        self.assertIn('exp', payload)
        self.assertIn('iat', payload)
    
    def test_decode_valid_token(self):
        """Test decoding valid JWT token."""
        user_id = 456
        username = "testuser2"
        
        token = generate_token(user_id, username)
        payload = decode_token(token)
        
        self.assertEqual(payload['user_id'], user_id)
        self.assertEqual(payload['username'], username)
    
    def test_decode_expired_token(self):
        """Test decoding expired JWT token."""
        # Create expired token
        payload = {
            'user_id': 789,
            'username': 'expireduser',
            'exp': datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        with self.assertRaises(Exception) as context:
            decode_token(expired_token)
        
        self.assertIn("expired", str(context.exception).lower())
    
    def test_decode_invalid_token(self):
        """Test decoding invalid JWT token."""
        invalid_token = "invalid.token.here"
        
        with self.assertRaises(Exception) as context:
            decode_token(invalid_token)
        
        self.assertIn("invalid", str(context.exception).lower())


class TestDatabaseFunctions(unittest.TestCase):
    """Test database operations for user management."""
    
    def setUp(self):
        """Set up test database before each test."""
        # Create temporary database file
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        
        # Patch the database path
        self.db_patcher = patch('auth.USERS_DB_PATH', self.test_db_path)
        self.db_patcher.start()
        
        # Initialize test database
        init_users_db()
    
    def tearDown(self):
        """Clean up test database after each test."""
        self.db_patcher.stop()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def test_init_users_db(self):
        """Test database initialization and default admin user creation."""
        # Check that database file exists
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Check that users table exists and has admin user
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'users')
        
        # Check admin user exists
        cursor.execute("SELECT username FROM users WHERE username='admin';")
        admin_user = cursor.fetchone()
        self.assertIsNotNone(admin_user)
        self.assertEqual(admin_user[0], 'admin')
        
        conn.close()
    
    def test_create_user_success(self):
        """Test successful user creation."""
        username = "newuser"
        password = "password123"
        email = "newuser@example.com"
        
        result = create_user(username, password, email)
        self.assertTrue(result)
        
        # Verify user was created in database
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()
        
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], username)
        self.assertEqual(user['email'], email)
    
    def test_create_user_duplicate_username(self):
        """Test user creation with duplicate username."""
        username = "duplicateuser"
        password = "password123"
        
        # Create user first time
        result1 = create_user(username, password)
        self.assertTrue(result1)
        
        # Try to create user with same username
        result2 = create_user(username, password)
        self.assertFalse(result2)
    
    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        username = "authuser"
        password = "authpass123"
        email = "authuser@example.com"
        
        # Create user first
        create_user(username, password, email)
        
        # Authenticate user
        user_info = authenticate_user(username, password)
        
        self.assertIsNotNone(user_info)
        self.assertEqual(user_info['username'], username)
        self.assertEqual(user_info['email'], email)
        self.assertIn('id', user_info)
    
    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password."""
        username = "authuser2"
        password = "correctpass"
        wrong_password = "wrongpass"
        
        # Create user
        create_user(username, password)
        
        # Try to authenticate with wrong password
        user_info = authenticate_user(username, wrong_password)
        
        self.assertIsNone(user_info)
    
    def test_authenticate_user_nonexistent(self):
        """Test authentication with nonexistent user."""
        user_info = authenticate_user("nonexistent", "password")
        self.assertIsNone(user_info)
    
    def test_authenticate_user_updates_last_login(self):
        """Test that successful authentication updates last_login timestamp."""
        username = "loginuser"
        password = "loginpass"
        
        # Create user
        create_user(username, password)
        
        # Check initial last_login is NULL
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        user_before = conn.execute(
            'SELECT last_login FROM users WHERE username = ?', (username,)
        ).fetchone()
        self.assertIsNone(user_before['last_login'])
        conn.close()
        
        # Authenticate user
        authenticate_user(username, password)
        
        # Check last_login was updated
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        user_after = conn.execute(
            'SELECT last_login FROM users WHERE username = ?', (username,)
        ).fetchone()
        self.assertIsNotNone(user_after['last_login'])
        conn.close()


class TestRequireAuthDecorator(unittest.TestCase):
    """Test the require_auth decorator."""
    
    @patch('auth.request')
    def test_require_auth_valid_token(self, mock_request):
        """Test require_auth decorator with valid token."""
        # Create a valid token
        user_id = 123
        username = "testuser"
        token = generate_token(user_id, username)
        
        # Mock request headers
        mock_request.headers.get.return_value = f"Bearer {token}"
        
        # Create a dummy function to decorate
        @require_auth
        def dummy_function():
            return "success"
        
        # Call the decorated function
        result = dummy_function()
        
        # Check that function executed successfully
        self.assertEqual(result, "success")
        
        # Check that current_user was set
        self.assertTrue(hasattr(mock_request, 'current_user'))
    
    @patch('auth.request')
    @patch('auth.jsonify')
    def test_require_auth_missing_token(self, mock_jsonify, mock_request):
        """Test require_auth decorator with missing token."""
        # Mock missing authorization header
        mock_request.headers.get.return_value = None
        mock_jsonify.return_value = ("Unauthorized", 401)
        
        # Create a dummy function to decorate
        @require_auth
        def dummy_function():
            return "success"
        
        # Call the decorated function
        result = dummy_function()
        
        # Check that jsonify was called with error
        mock_jsonify.assert_called_once()
        self.assertEqual(result, ("Unauthorized", 401))
    
    @patch('auth.request')
    @patch('auth.jsonify')
    def test_require_auth_invalid_token(self, mock_jsonify, mock_request):
        """Test require_auth decorator with invalid token."""
        # Mock invalid token
        mock_request.headers.get.return_value = "Bearer invalid_token"
        mock_jsonify.return_value = ("Unauthorized", 401)
        
        # Create a dummy function to decorate
        @require_auth
        def dummy_function():
            return "success"
        
        # Call the decorated function
        result = dummy_function()
        
        # Check that jsonify was called with error
        mock_jsonify.assert_called_once()
        self.assertEqual(result, ("Unauthorized", 401))


if __name__ == '__main__':
    unittest.main()
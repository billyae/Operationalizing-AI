"""
Unit tests for Flask application endpoints.

This module tests API endpoints, request handling, error responses,
and integration with authentication system.
"""

import unittest
import json
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app import app
from auth import create_user, generate_token, init_users_db


class TestFlaskApp(unittest.TestCase):
    """Test Flask application endpoints and functionality."""
    
    def setUp(self):
        """Set up test client and test database before each test."""
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Create test client
        self.client = app.test_client()
        
        # Create temporary database
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        
        # Patch the database path
        self.db_patcher = patch('auth.USERS_DB_PATH', self.test_db_path)
        self.db_patcher.start()
        
        # Initialize test database
        init_users_db()
        
        # Create test user
        self.test_username = "testuser"
        self.test_password = "testpass123"
        self.test_email = "test@example.com"
        create_user(self.test_username, self.test_password, self.test_email)
        
        # Generate test token
        self.test_token = generate_token(1, self.test_username)
    
    def tearDown(self):
        """Clean up after each test."""
        self.db_patcher.stop()
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/api/health')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
    
    def test_login_success(self):
        """Test successful user login."""
        login_data = {
            'username': self.test_username,
            'password': self.test_password
        }
        
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], self.test_username)
        self.assertEqual(data['message'], 'Login successful')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {
            'username': self.test_username,
            'password': 'wrongpassword'
        }
        
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid username or password')
    
    def test_login_missing_data(self):
        """Test login with missing username or password."""
        login_data = {
            'username': self.test_username
            # Missing password
        }
        
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Username and password are required')
    
    def test_register_success(self):
        """Test successful user registration."""
        register_data = {
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'newuser@example.com'
        }
        
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps(register_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Registration successful')
    
    def test_register_duplicate_username(self):
        """Test registration with existing username."""
        register_data = {
            'username': self.test_username,  # Already exists
            'password': 'newpass123',
            'email': 'duplicate@example.com'
        }
        
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps(register_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 409)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Username already exists')
    
    def test_register_short_password(self):
        """Test registration with password too short."""
        register_data = {
            'username': 'shortpassuser',
            'password': '12345',  # Too short
            'email': 'short@example.com'
        }
        
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps(register_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Password must be at least 6 characters')
    
    def test_verify_token_valid(self):
        """Test token verification with valid token."""
        headers = {'Authorization': f'Bearer {self.test_token}'}
        
        response = self.client.get('/api/auth/verify', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['valid'])
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], self.test_username)
    
    def test_verify_token_missing(self):
        """Test token verification without token."""
        response = self.client.get('/api/auth/verify')
        
        self.assertEqual(response.status_code, 401)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Token is missing')
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        headers = {'Authorization': 'Bearer invalid_token'}
        
        response = self.client.get('/api/auth/verify', headers=headers)
        
        self.assertEqual(response.status_code, 401)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    @patch('app.query_bedrock')
    def test_chat_endpoint_success(self, mock_query_bedrock):
        """Test chat endpoint with valid request."""
        mock_query_bedrock.return_value = "Hello! How can I help you?"
        
        chat_data = {
            'messages': [
                {'role': 'user', 'content': 'Hello'}
            ],
            'aws_credentials': {
                'access_key': 'test_access_key',
                'secret_key': 'test_secret_key'
            }
        }
        
        headers = {'Authorization': f'Bearer {self.test_token}'}
        
        response = self.client.post(
            '/api/chat',
            data=json.dumps(chat_data),
            content_type='application/json',
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('reply', data)
        self.assertIn('success', data)
        self.assertIn('latency_ms', data)
        self.assertTrue(data['success'])
    
    def test_chat_endpoint_missing_auth(self):
        """Test chat endpoint without authentication."""
        chat_data = {
            'messages': [{'role': 'user', 'content': 'Hello'}],
            'aws_credentials': {
                'access_key': 'test_access_key',
                'secret_key': 'test_secret_key'
            }
        }
        
        response = self.client.post(
            '/api/chat',
            data=json.dumps(chat_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_chat_endpoint_missing_credentials(self):
        """Test chat endpoint without AWS credentials."""
        chat_data = {
            'messages': [{'role': 'user', 'content': 'Hello'}]
            # Missing aws_credentials
        }
        
        headers = {'Authorization': f'Bearer {self.test_token}'}
        
        response = self.client.post(
            '/api/chat',
            data=json.dumps(chat_data),
            content_type='application/json',
            headers=headers
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'AWS credentials are required')
    
    @patch('app.fetch_all_invocations')
    def test_metrics_endpoint(self, mock_fetch_invocations):
        """Test metrics endpoint."""
        mock_fetch_invocations.return_value = [
            {
                'id': 1,
                'timestamp': '2024-01-01T10:00:00',
                'latency_ms': 150.5,
                'success': True
            }
        ]
        
        headers = {'Authorization': f'Bearer {self.test_token}'}
        
        response = self.client.get('/api/metrics', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('invocations', data)
        self.assertEqual(len(data['invocations']), 1)
    
    def test_metrics_endpoint_missing_auth(self):
        """Test metrics endpoint without authentication."""
        response = self.client.get('/api/metrics')
        
        self.assertEqual(response.status_code, 401)
    
    def test_404_handler(self):
        """Test 404 error handler."""
        response = self.client.get('/api/nonexistent')
        
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Endpoint not found')


if __name__ == '__main__':
    unittest.main()
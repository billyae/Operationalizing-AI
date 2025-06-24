"""
Unit tests for frontend functions.

This module tests the Streamlit frontend application functions including
authentication, chat interface, and API communication.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import requests
import sys
import os
import json

# Add frontend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../frontend'))

# Mock streamlit before importing app
with patch.dict('sys.modules', {'streamlit': MagicMock()}):
    from app import (
        login_user, register_user, get_chat_response, 
        get_metrics, logout_user, init_session_state
    )


class TestAuthenticationFunctions(unittest.TestCase):
    """Test user authentication functions."""
    
    @patch('app.requests.post')
    def test_login_user_success(self, mock_post):
        """Test successful user login."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_token_123',
            'user': {'id': 1, 'username': 'testuser'}
        }
        mock_post.return_value = mock_response
        
        username = "testuser"
        password = "testpass"
        
        result = login_user(username, password)
        
        # Check that request was made correctly
        mock_post.assert_called_once_with(
            'http://localhost:5000/auth/login',
            json={'username': username, 'password': password}
        )
        
        # Check return value
        self.assertIsNotNone(result)
        self.assertEqual(result['access_token'], 'test_token_123')
        self.assertEqual(result['user']['username'], 'testuser')
    
    @patch('app.requests.post')
    def test_login_user_invalid_credentials(self, mock_post):
        """Test login with invalid credentials."""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'message': 'Invalid credentials'}
        mock_post.return_value = mock_response
        
        result = login_user("wronguser", "wrongpass")
        
        self.assertIsNone(result)
    
    @patch('app.requests.post')
    def test_login_user_connection_error(self, mock_post):
        """Test login with connection error."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = login_user("testuser", "testpass")
        
        self.assertIsNone(result)
    
    @patch('app.requests.post')
    def test_register_user_success(self, mock_post):
        """Test successful user registration."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'message': 'User created successfully'}
        mock_post.return_value = mock_response
        
        username = "newuser"
        password = "newpass"
        email = "newuser@example.com"
        
        result = register_user(username, password, email)
        
        # Check that request was made correctly
        mock_post.assert_called_once_with(
            'http://localhost:5000/auth/register',
            json={'username': username, 'password': password, 'email': email}
        )
        
        self.assertTrue(result)
    
    @patch('app.requests.post')
    def test_register_user_username_exists(self, mock_post):
        """Test registration with existing username."""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'message': 'Username already exists'}
        mock_post.return_value = mock_response
        
        result = register_user("existinguser", "password", "email@example.com")
        
        self.assertFalse(result)
    
    @patch('app.requests.post')
    def test_register_user_connection_error(self, mock_post):
        """Test registration with connection error."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = register_user("testuser", "testpass", "test@example.com")
        
        self.assertFalse(result)
    
    @patch('app.st')
    def test_logout_user(self, mock_st):
        """Test user logout functionality."""
        # Mock session state
        mock_session_state = {
            'authenticated': True,
            'user_token': 'test_token',
            'user_info': {'username': 'testuser'}
        }
        mock_st.session_state = mock_session_state
        
        logout_user()
        
        # Check that session state was cleared
        self.assertFalse(mock_session_state.get('authenticated', False))
        self.assertIsNone(mock_session_state.get('user_token'))
        self.assertIsNone(mock_session_state.get('user_info'))


class TestChatFunctions(unittest.TestCase):
    """Test chat-related functions."""
    
    @patch('app.requests.post')
    def test_get_chat_response_success(self, mock_post):
        """Test successful chat response."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': 'Hello! How can I help you today?'
        }
        mock_post.return_value = mock_response
        
        message = "Hello"
        token = "test_token"
        
        result = get_chat_response(message, token)
        
        # Check that request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], 'http://localhost:5000/chat')
        self.assertEqual(call_args[1]['json']['message'], message)
        self.assertEqual(call_args[1]['headers']['Authorization'], f'Bearer {token}')
        
        # Check return value
        self.assertEqual(result, 'Hello! How can I help you today?')
    
    @patch('app.requests.post')
    def test_get_chat_response_unauthorized(self, mock_post):
        """Test chat response with unauthorized token."""
        # Mock unauthorized response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'message': 'Unauthorized'}
        mock_post.return_value = mock_response
        
        result = get_chat_response("Hello", "invalid_token")
        
        self.assertIn("Authentication failed", result)
    
    @patch('app.requests.post')
    def test_get_chat_response_server_error(self, mock_post):
        """Test chat response with server error."""
        # Mock server error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'message': 'Internal server error'}
        mock_post.return_value = mock_response
        
        result = get_chat_response("Hello", "test_token")
        
        self.assertIn("服务器错误", result)
    
    @patch('app.requests.post')
    def test_get_chat_response_connection_error(self, mock_post):
        """Test chat response with connection error."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = get_chat_response("Hello", "test_token")
        
        self.assertIn("连接失败", result)


class TestMetricsFunctions(unittest.TestCase):
    """Test metrics-related functions."""
    
    @patch('app.requests.get')
    def test_get_metrics_success(self, mock_get):
        """Test successful metrics retrieval."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'total_invocations': 100,
            'total_tokens': 50000,
            'average_response_time': 1.5,
            'recent_invocations': [
                {'model_id': 'claude-3', 'timestamp': '2024-01-01T10:00:00'},
                {'model_id': 'claude-3', 'timestamp': '2024-01-01T09:30:00'}
            ]
        }
        mock_get.return_value = mock_response
        
        token = "test_token"
        
        result = get_metrics(token)
        
        # Check that request was made correctly
        mock_get.assert_called_once_with(
            'http://localhost:5000/metrics',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        # Check return value
        self.assertIsNotNone(result)
        self.assertEqual(result['total_invocations'], 100)
        self.assertEqual(result['total_tokens'], 50000)
        self.assertEqual(len(result['recent_invocations']), 2)
    
    @patch('app.requests.get')
    def test_get_metrics_unauthorized(self, mock_get):
        """Test metrics retrieval with unauthorized token."""
        # Mock unauthorized response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'message': 'Unauthorized'}
        mock_get.return_value = mock_response
        
        result = get_metrics("invalid_token")
        
        self.assertIsNone(result)
    
    @patch('app.requests.get')
    def test_get_metrics_connection_error(self, mock_get):
        """Test metrics retrieval with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = get_metrics("test_token")
        
        self.assertIsNone(result)


class TestSessionStateFunctions(unittest.TestCase):
    """Test session state management functions."""
    
    @patch('app.st')
    def test_init_session_state(self, mock_st):
        """Test session state initialization."""
        # Mock empty session state
        mock_st.session_state = {}
        
        init_session_state()
        
        # Check that default values were set
        expected_keys = [
            'authenticated', 'user_token', 'user_info', 
            'chat_history', 'current_page'
        ]
        
        for key in expected_keys:
            self.assertIn(key, mock_st.session_state)
        
        # Check default values
        self.assertFalse(mock_st.session_state['authenticated'])
        self.assertIsNone(mock_st.session_state['user_token'])
        self.assertIsNone(mock_st.session_state['user_info'])
        self.assertEqual(mock_st.session_state['chat_history'], [])
        self.assertEqual(mock_st.session_state['current_page'], 'login')
    
    @patch('app.st')
    def test_init_session_state_existing_values(self, mock_st):
        """Test session state initialization with existing values."""
        # Mock session state with existing values
        mock_st.session_state = {
            'authenticated': True,
            'user_token': 'existing_token',
            'chat_history': [{'user': 'Hello', 'bot': 'Hi there!'}]
        }
        
        init_session_state()
        
        # Check that existing values were preserved
        self.assertTrue(mock_st.session_state['authenticated'])
        self.assertEqual(mock_st.session_state['user_token'], 'existing_token')
        self.assertEqual(len(mock_st.session_state['chat_history']), 1)
        
        # Check that missing keys were added with defaults
        self.assertIn('current_page', mock_st.session_state)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios with multiple functions."""
    
    @patch('app.requests.post')
    @patch('app.st')
    def test_complete_auth_flow(self, mock_st, mock_post):
        """Test complete authentication flow from login to logout."""
        # Mock session state
        mock_st.session_state = {}
        
        # Initialize session
        init_session_state()
        
        # Mock successful login response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_token_123',
            'user': {'id': 1, 'username': 'testuser'}
        }
        mock_post.return_value = mock_response
        
        # Test login
        login_result = login_user("testuser", "testpass")
        self.assertIsNotNone(login_result)
        
        # Simulate setting session state after login
        mock_st.session_state['authenticated'] = True
        mock_st.session_state['user_token'] = login_result['access_token']
        mock_st.session_state['user_info'] = login_result['user']
        
        # Test logout
        logout_user()
        
        # Verify logout cleared session
        self.assertFalse(mock_st.session_state.get('authenticated', False))
    
    @patch('app.requests.post')
    def test_chat_with_different_scenarios(self, mock_post):
        """Test chat function with various response scenarios."""
        token = "test_token"
        
        # Test successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'Success message'}
        mock_post.return_value = mock_response
        
        result = get_chat_response("Hello", token)
        self.assertEqual(result, 'Success message')
        
        # Test error response
        mock_response.status_code = 500
        mock_response.json.return_value = {'message': 'Server error'}
        mock_post.return_value = mock_response
        
        result = get_chat_response("Hello", token)
        self.assertIn("服务器错误", result)


if __name__ == '__main__':
    unittest.main() 
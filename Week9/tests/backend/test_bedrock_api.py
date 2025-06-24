"""
Unit tests for Bedrock API module.

This module tests AWS Bedrock integration, payload building, client initialization,
and query functions with error handling.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import json
import sys
import os
from botocore.exceptions import ClientError, NoCredentialsError

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from bedrock_api import build_anthropic_payload, get_bedrock_client, query_bedrock


class TestBuildAnthropicPayload(unittest.TestCase):
    """Test the Anthropic payload building function."""
    
    def test_build_anthropic_payload_simple_message(self):
        """Test building payload with simple message."""
        user_message = "Hello, how are you?"
        
        payload = build_anthropic_payload(user_message)
        
        self.assertIsInstance(payload, dict)
        self.assertIn('anthropic_version', payload)
        self.assertIn('max_tokens', payload)
        self.assertIn('messages', payload)
        
        # Check messages structure
        messages = payload['messages']
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['role'], 'user')
        self.assertEqual(messages[0]['content'], user_message)
    
    def test_build_anthropic_payload_with_system_prompt(self):
        """Test building payload with system prompt."""
        user_message = "What is the weather today?"
        system_prompt = "You are a helpful weather assistant."
        
        payload = build_anthropic_payload(user_message, system_prompt=system_prompt)
        
        self.assertIn('system', payload)
        self.assertEqual(payload['system'], system_prompt)
    
    def test_build_anthropic_payload_default_values(self):
        """Test that payload contains expected default values."""
        user_message = "Test message"
        
        payload = build_anthropic_payload(user_message)
        
        # Check default values are present
        self.assertEqual(payload['anthropic_version'], 'bedrock-2023-05-31')
        self.assertGreater(payload['max_tokens'], 0)
        self.assertIsInstance(payload['max_tokens'], int)
    
    def test_build_anthropic_payload_custom_max_tokens(self):
        """Test building payload with custom max_tokens."""
        user_message = "Test message"
        custom_max_tokens = 500
        
        payload = build_anthropic_payload(user_message, max_tokens=custom_max_tokens)
        
        self.assertEqual(payload['max_tokens'], custom_max_tokens)
    
    def test_build_anthropic_payload_empty_message(self):
        """Test building payload with empty message."""
        user_message = ""
        
        payload = build_anthropic_payload(user_message)
        
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload['messages'][0]['content'], "")


class TestGetBedrockClient(unittest.TestCase):
    """Test the Bedrock client initialization function."""
    
    @patch('bedrock_api.boto3.client')
    def test_get_bedrock_client_success(self, mock_boto_client):
        """Test successful Bedrock client creation."""
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        
        client = get_bedrock_client()
        
        # Check that boto3.client was called with correct parameters
        mock_boto_client.assert_called_once_with(
            'bedrock-runtime', 
            region_name='us-east-1'
        )
        self.assertEqual(client, mock_client)
    
    @patch('bedrock_api.boto3.client')
    def test_get_bedrock_client_custom_region(self, mock_boto_client):
        """Test Bedrock client creation with custom region."""
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        custom_region = 'us-west-2'
        
        with patch.dict(os.environ, {'AWS_REGION': custom_region}):
            client = get_bedrock_client()
        
        mock_boto_client.assert_called_once_with(
            'bedrock-runtime', 
            region_name=custom_region
        )
        self.assertEqual(client, mock_client)
    
    @patch('bedrock_api.boto3.client')
    def test_get_bedrock_client_no_credentials(self, mock_boto_client):
        """Test Bedrock client creation with no credentials."""
        mock_boto_client.side_effect = NoCredentialsError()
        
        with self.assertRaises(NoCredentialsError):
            get_bedrock_client()


class TestQueryBedrock(unittest.TestCase):
    """Test the Bedrock query function."""
    
    @patch('bedrock_api.get_bedrock_client')
    @patch('bedrock_api.record_invocation')
    def test_query_bedrock_success(self, mock_record_invocation, mock_get_client):
        """Test successful Bedrock query."""
        # Mock client and response
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = {
            'body': MagicMock()
        }
        mock_response_body = {
            'content': [{'text': 'Hello! How can I help you?'}]
        }
        mock_response['body'].read.return_value = json.dumps(mock_response_body).encode()
        mock_client.invoke_model.return_value = mock_response
        
        user_message = "Hello"
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        result = query_bedrock(user_message, model_id)
        
        # Check that invoke_model was called correctly
        mock_client.invoke_model.assert_called_once()
        call_args = mock_client.invoke_model.call_args
        self.assertEqual(call_args[1]['modelId'], model_id)
        self.assertEqual(call_args[1]['contentType'], 'application/json')
        
        # Check that payload was built correctly
        payload = json.loads(call_args[1]['body'])
        self.assertIn('messages', payload)
        self.assertEqual(payload['messages'][0]['content'], user_message)
        
        # Check return value
        self.assertEqual(result, 'Hello! How can I help you?')
        
        # Check that invocation was recorded
        mock_record_invocation.assert_called_once()
    
    @patch('bedrock_api.get_bedrock_client')
    @patch('bedrock_api.record_invocation')
    def test_query_bedrock_with_system_prompt(self, mock_record_invocation, mock_get_client):
        """Test Bedrock query with system prompt."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_response = {
            'body': MagicMock()
        }
        mock_response_body = {
            'content': [{'text': 'I am a helpful assistant.'}]
        }
        mock_response['body'].read.return_value = json.dumps(mock_response_body).encode()
        mock_client.invoke_model.return_value = mock_response
        
        user_message = "Who are you?"
        system_prompt = "You are a helpful AI assistant."
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        result = query_bedrock(user_message, model_id, system_prompt=system_prompt)
        
        # Check that payload includes system prompt
        call_args = mock_client.invoke_model.call_args
        payload = json.loads(call_args[1]['body'])
        self.assertIn('system', payload)
        self.assertEqual(payload['system'], system_prompt)
        
        self.assertEqual(result, 'I am a helpful assistant.')
    
    @patch('bedrock_api.get_bedrock_client')
    @patch('bedrock_api.record_invocation')
    @patch('bedrock_api.time.sleep')
    def test_query_bedrock_retry_on_client_error(self, mock_sleep, mock_record_invocation, mock_get_client):
        """Test Bedrock query retry mechanism on ClientError."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock ClientError on first two calls, success on third
        client_error = ClientError(
            error_response={'Error': {'Code': 'ThrottlingException'}},
            operation_name='InvokeModel'
        )
        
        mock_response = {
            'body': MagicMock()
        }
        mock_response_body = {
            'content': [{'text': 'Success after retry'}]
        }
        mock_response['body'].read.return_value = json.dumps(mock_response_body).encode()
        
        mock_client.invoke_model.side_effect = [
            client_error,
            client_error,
            mock_response
        ]
        
        user_message = "Test message"
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        result = query_bedrock(user_message, model_id)
        
        # Check that invoke_model was called 3 times (2 failures + 1 success)
        self.assertEqual(mock_client.invoke_model.call_count, 3)
        
        # Check that sleep was called for retries
        self.assertEqual(mock_sleep.call_count, 2)
        
        # Check final result
        self.assertEqual(result, 'Success after retry')
    
    @patch('bedrock_api.get_bedrock_client')
    @patch('bedrock_api.record_invocation')
    @patch('bedrock_api.time.sleep')
    def test_query_bedrock_max_retries_exceeded(self, mock_sleep, mock_record_invocation, mock_get_client):
        """Test Bedrock query when max retries are exceeded."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock ClientError on all calls
        client_error = ClientError(
            error_response={'Error': {'Code': 'ThrottlingException'}},
            operation_name='InvokeModel'
        )
        mock_client.invoke_model.side_effect = client_error
        
        user_message = "Test message"
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        with self.assertRaises(ClientError):
            query_bedrock(user_message, model_id)
        
        # Check that invoke_model was called max_retries + 1 times
        expected_calls = 4  # 1 initial + 3 retries
        self.assertEqual(mock_client.invoke_model.call_count, expected_calls)
    
    @patch('bedrock_api.get_bedrock_client')
    @patch('bedrock_api.record_invocation')
    def test_query_bedrock_malformed_response(self, mock_record_invocation, mock_get_client):
        """Test Bedrock query with malformed response."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock response with missing content
        mock_response = {
            'body': MagicMock()
        }
        mock_response_body = {'malformed': 'response'}
        mock_response['body'].read.return_value = json.dumps(mock_response_body).encode()
        mock_client.invoke_model.return_value = mock_response
        
        user_message = "Test message"
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        result = query_bedrock(user_message, model_id)
        
        # Should return error message for malformed response
        self.assertIn("Unexpected response format", result)
    
    @patch('bedrock_api.get_bedrock_client')
    @patch('bedrock_api.record_invocation')
    def test_query_bedrock_json_decode_error(self, mock_record_invocation, mock_get_client):
        """Test Bedrock query with JSON decode error."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock response with invalid JSON
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'invalid json content'
        mock_client.invoke_model.return_value = mock_response
        
        user_message = "Test message"
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        result = query_bedrock(user_message, model_id)
        
        # Should return error message for JSON decode error
        self.assertIn("Failed to parse response", result)
    
    @patch('bedrock_api.get_bedrock_client')
    def test_query_bedrock_get_client_error(self, mock_get_client):
        """Test Bedrock query when client initialization fails."""
        mock_get_client.side_effect = Exception("Client initialization failed")
        
        user_message = "Test message"
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        result = query_bedrock(user_message, model_id)
        
        # Should return error message for client initialization failure
        self.assertIn("Error", result)


if __name__ == '__main__':
    unittest.main() 
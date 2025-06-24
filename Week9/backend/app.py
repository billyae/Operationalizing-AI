"""
Flask backend application for Bedrock Chatbot.

This module provides a REST API backend for the chatbot application with features including:
- User authentication and authorization
- AWS Bedrock integration for AI conversations
- Metrics collection and monitoring
- Health checks and error handling

Author: AI Assistant
Date: 2024
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS
from metrics import record_invocation 
from bedrock_api import query_bedrock
import logging_config
from auth import require_auth, authenticate_user, create_user, generate_token

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Starting Bedrock Chatbot Flask backend")

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication


def set_aws_credentials_in_env(access_key: str, secret_key: str) -> None:
    """
    Store AWS credentials in environment variables for Bedrock API access.
    
    This function sets AWS credentials in environment variables so that
    the query_bedrock() function can pick them up at call time.
    
    Args:
        access_key (str): AWS Access Key ID
        secret_key (str): AWS Secret Access Key
        
    Returns:
        None
    """
    os.environ["AWS_ACCESS_KEY_ID"] = access_key
    os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key
    # Ensure no stale session token is present
    os.environ.pop("AWS_SESSION_TOKEN", None)


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring system status.
    
    Returns:
        JSON response with status and timestamp
    """
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    User login endpoint for authentication.
    
    Expected JSON payload:
    {
        "username": "string",
        "password": "string"
    }
    
    Returns:
        JSON response with JWT token and user info on success,
        error message on failure
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Validate required fields
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        # Authenticate user
        user = authenticate_user(username, password)
        if user:
            token = generate_token(user['id'], user['username'])
            return jsonify({
                "token": token,
                "user": user,
                "message": "Login successful"
            })
        else:
            return jsonify({"error": "Invalid username or password"}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({"error": "Login failed"}), 500


@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    User registration endpoint for creating new accounts.
    
    Expected JSON payload:
    {
        "username": "string",
        "password": "string",
        "email": "string" (optional)
    }
    
    Returns:
        JSON response with success message or error
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        # Validate required fields
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Create new user
        success = create_user(username, password, email)
        if success:
            return jsonify({"message": "Registration successful"})
        else:
            return jsonify({"error": "Username already exists"}), 409
            
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({"error": "Registration failed"}), 500


@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify_token():
    """
    Token verification endpoint for validating JWT tokens.
    
    Requires valid JWT token in Authorization header.
    
    Returns:
        JSON response with token validity and user info
    """
    return jsonify({
        "valid": True,
        "user": {
            "id": request.current_user['user_id'],
            "username": request.current_user['username']
        }
    })


@app.route('/api/chat', methods=['POST'])
@require_auth
def chat_endpoint():
    """
    Chat processing endpoint for AI conversations (requires authentication).
    
    This endpoint handles chat requests, integrates with AWS Bedrock,
    and records metrics for monitoring.
    
    Expected JSON payload:
    {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        "aws_credentials": {
            "access_key": "your_access_key",
            "secret_key": "your_secret_key"
        }
    }
    
    Returns:
        JSON response with AI reply, success status, and latency metrics
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        messages = data.get('messages', [])
        aws_credentials = data.get('aws_credentials', {})
        
        # Validate required fields
        if not messages:
            return jsonify({"error": "Messages array is required"}), 400
            
        access_key = aws_credentials.get('access_key')
        secret_key = aws_credentials.get('secret_key')
        
        if not access_key or not secret_key:
            return jsonify({"error": "AWS credentials are required"}), 400
        
        # Set AWS credentials for Bedrock API
        set_aws_credentials_in_env(access_key, secret_key)
        
        # Process chat request with timing
        start_time = datetime.now()
        success = False
        
        try:
            assistant_reply = query_bedrock(messages)
            success = True
        except Exception as e:
            logger.error(f"Error calling Bedrock: {e}", exc_info=True)
            assistant_reply = "❗ Sorry, I encountered an error."
            
        end_time = datetime.now()
        
        # Record metrics with user info
        latency_ms = (end_time - start_time).total_seconds() * 1000.0
        record_invocation(latency_ms=latency_ms, success=success)
        
        # Log user activity
        logger.info(
            f"Chat request from user {request.current_user['username']}, "
            f"latency: {latency_ms:.1f}ms, success: {success}"
        )
        
        return jsonify({
            "reply": assistant_reply,
            "success": success,
            "latency_ms": latency_ms
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/metrics', methods=['GET'])
@require_auth
def get_metrics():
    """
    Metrics data endpoint for monitoring dashboard (requires authentication).
    
    Returns:
        JSON response with invocation metrics and statistics
    """
    try:
        from metrics import fetch_all_invocations
        invocations = fetch_all_invocations()
        
        # Log metrics access
        logger.info(f"Metrics accessed by user {request.current_user['username']}")
        
        return jsonify({"invocations": invocations})
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch metrics"}), 500


@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 Not Found errors.
    
    Args:
        error: Flask error object
        
    Returns:
        JSON error response
    """
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 Internal Server Error.
    
    Args:
        error: Flask error object
        
    Returns:
        JSON error response
    """
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Production environment configuration
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5001))
    
    logger.info(f"Starting Flask server on port {port}, debug={debug_mode}")
    
    app.run(debug=debug_mode, host="0.0.0.0", port=port) 
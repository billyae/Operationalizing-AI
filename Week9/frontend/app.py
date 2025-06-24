"""
Streamlit frontend application for Bedrock Chatbot.

This module provides a web-based user interface for the chatbot application with features including:
- User authentication (login/registration)
- Real-time chat interface with AI
- Monitoring dashboard with metrics visualization
- AWS credentials management

Author: AI Assistant
Date: 2024
"""

import streamlit as st
import pandas as pd
import requests
import json
import time
import os
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="🤖 Bedrock Chatbot & Monitoring Dashboard",
    page_icon="🤖",
    layout="wide"
)

# Backend API base URL
BACKEND_URL = "http://localhost:5001"


def init_session_state():
    """
    Initialize Streamlit session state variables.
    
    Sets up default values for authentication, user data, and chat messages
    if they don't already exist in the session state.
    
    Returns:
        None
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "token" not in st.session_state:
        st.session_state["token"] = None
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "messages" not in st.session_state:
        st.session_state["messages"] = []


def login_user(username: str, password: str) -> dict:
    """
    Authenticate user with backend login API.
    
    Args:
        username (str): User's username
        password (str): User's password
        
    Returns:
        dict: Response from backend API containing token/user info or error
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        return response.json() if response.status_code == 200 else {
            "error": response.json().get("error", "Login failed")
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection failed: {str(e)}"}


def register_user(username: str, password: str, email: str) -> dict:
    """
    Register new user with backend registration API.
    
    Args:
        username (str): Desired username
        password (str): User's password
        email (str): User's email address
        
    Returns:
        dict: Response from backend API containing success message or error
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/register",
            json={"username": username, "password": password, "email": email},
            timeout=10
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection failed: {str(e)}"}


def verify_token() -> bool:
    """
    Verify if the current JWT token is still valid.
    
    Returns:
        bool: True if token is valid, False otherwise
    """
    if not st.session_state.get("token"):
        return False
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state['token']}"}
        response = requests.get(
            f"{BACKEND_URL}/api/auth/verify", 
            headers=headers, 
            timeout=5
        )
        return response.status_code == 200
    except:
        return False


def call_backend_chat(messages: list, aws_access_key: str, aws_secret_key: str) -> dict:
    """
    Send chat request to backend API with authentication.
    
    Args:
        messages (list): List of chat messages
        aws_access_key (str): AWS access key for Bedrock
        aws_secret_key (str): AWS secret key for Bedrock
        
    Returns:
        dict: Response from backend containing AI reply or error
    """
    try:
        headers = {"Authorization": f"Bearer {st.session_state['token']}"}
        payload = {
            "messages": messages,
            "aws_credentials": {
                "access_key": aws_access_key,
                "secret_key": aws_secret_key
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Backend error: {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"Backend connection failed: {str(e)}"}


def get_metrics_from_backend() -> dict:
    """
    Fetch metrics data from backend API with authentication.
    
    Returns:
        dict: Metrics data from backend or error message
    """
    try:
        headers = {"Authorization": f"Bearer {st.session_state['token']}"}
        response = requests.get(
            f"{BACKEND_URL}/api/metrics", 
            headers=headers, 
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to fetch metrics: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Backend connection failed: {str(e)}"}


def render_login_page():
    """
    Render the login/registration page interface.
    
    Displays login and registration forms with backend connectivity check.
    Handles user authentication and provides default admin credentials info.
    
    Returns:
        None
    """
    st.title("🔐 User Authentication")
    
    # Check backend connectivity
    try:
        health_response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ Backend connection is healthy")
        else:
            st.error("❌ Backend response error")
            return
    except:
        st.error("❌ Unable to connect to backend service. Please ensure backend is running on localhost:5000")
        return
    
    # Create login and registration tabs
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login:
                if username and password:
                    result = login_user(username, password)
                    if "token" in result:
                        st.session_state["authenticated"] = True
                        st.session_state["token"] = result["token"]
                        st.session_state["user"] = result["user"]
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(result.get("error", "Login failed"))
                else:
                    st.error("Please enter username and password")
    
    with tab2:
        st.subheader("Register New User")
        with st.form("register_form"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            email = st.text_input("Email (Optional)")
            submit_register = st.form_submit_button("Register")
            
            if submit_register:
                if new_username and new_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        result = register_user(new_username, new_password, email)
                        if "message" in result:
                            st.success("Registration successful! Please switch to login tab.")
                        else:
                            st.error(result.get("error", "Registration failed"))
                else:
                    st.error("Please enter username and password")
    
    # Default admin credentials info
    st.info("""
    🎯 **Quick Start** - Default Admin Account:
    - Username: `admin`
    - Password: `admin123`
    """)


def render_chat_history():
    """
    Render the chat message history in the chat interface.
    
    Displays all messages from the current session's chat history
    using Streamlit's chat message components.
    
    Returns:
        None
    """
    for msg in st.session_state["messages"]:
        st.chat_message(msg["role"]).write(msg["content"])


def render_metrics_dashboard():
    """
    Render the monitoring dashboard with real-time metrics.
    
    Displays system metrics including request counts, latency, success rates,
    and interactive charts for performance monitoring.
    
    Returns:
        None
    """
    st.subheader("📊 Real-time Monitoring Dashboard")
    
    # Fetch metrics data from backend
    metrics_data = get_metrics_from_backend()
    
    if "error" in metrics_data:
        st.error(f"Unable to fetch metrics data: {metrics_data['error']}")
        return
    
    invocations = metrics_data.get("invocations", [])
    
    if not invocations:
        st.warning("No metrics data available. Start chatting to see statistics.")
        return
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(invocations)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['minute'] = df['timestamp'].dt.floor('min')
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", len(df))
    
    with col2:
        avg_latency = df['latency_ms'].mean()
        st.metric("Average Latency (ms)", f"{avg_latency:.1f}")
    
    with col3:
        success_rate = (df['success'].sum() / len(df)) * 100
        st.metric("Success Rate (%)", f"{success_rate:.1f}")
    
    with col4:
        recent_requests = len(df[df['timestamp'] > (datetime.now() - pd.Timedelta(minutes=5))])
        st.metric("Last 5 Minutes", recent_requests)
    
    # Generate time-series charts
    if len(df) > 1:
        per_minute = df.groupby('minute').agg({
            'id': 'count',
            'latency_ms': 'mean',
            'success': lambda x: 1.0 - x.mean()  # Error rate
        }).rename(columns={
            'id': 'requests_per_minute',
            'latency_ms': 'avg_latency_ms',
            'success': 'error_rate'
        }).reset_index()
        
        # Display charts in two columns
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("Requests per Minute")
            st.line_chart(per_minute.set_index('minute')['requests_per_minute'])
            
            st.subheader("Average Latency (ms)")
            st.line_chart(per_minute.set_index('minute')['avg_latency_ms'])
        
        with chart_col2:
            st.subheader("Error Rate")
            st.line_chart(per_minute.set_index('minute')['error_rate'])
            
            st.subheader("Recent Request Records")
            recent_df = df.sort_values('timestamp', ascending=False).head(10)
            st.dataframe(
                recent_df[['timestamp', 'latency_ms', 'success']], 
                use_container_width=True
            )


def render_main_app():
    """
    Render the main application interface for authenticated users.
    
    Displays the chat interface, monitoring dashboard, user information,
    and AWS credentials management in a tabbed layout.
    
    Returns:
        None
    """
    # Page title
    st.title("🤖 Bedrock Chatbot & Monitoring Dashboard")
    
    # Sidebar - User info and AWS credentials
    with st.sidebar:
        # User information
        st.header(f"👤 Welcome, {st.session_state['user']['username']}")
        if st.button("🚪 Logout"):
            st.session_state["authenticated"] = False
            st.session_state["token"] = None
            st.session_state["user"] = None
            st.session_state["messages"] = []
            st.rerun()
        
        st.markdown("---")
        
        # AWS credentials input
        st.header("🔑 AWS Credentials")
        aws_access_key = st.text_input(
            "Access Key ID", 
            key="aws_access_key", 
            type="password"
        )
        aws_secret_key = st.text_input(
            "Secret Access Key", 
            key="aws_secret_key", 
            type="password"
        )
    
    # Create main content tabs
    tab1, tab2 = st.tabs(["💬 Chat Interface", "📊 Monitoring Dashboard"])
    
    with tab1:
        st.markdown("### Chat with Bedrock Claude")
        st.markdown("Enter your message below to start a conversation...")
        
        # Render existing chat history
        render_chat_history()
        
        # Handle new user input
        prompt = st.chat_input("Enter your message...")
        if prompt:
            # Validate AWS credentials
            if not aws_access_key or not aws_secret_key:
                st.error("🔒 Please enter AWS credentials in the sidebar")
                st.stop()
            
            # Add user message to history
            st.session_state["messages"].append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            # Process AI response
            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.write("⏳ Thinking...")
                
                response = call_backend_chat(
                    st.session_state["messages"],
                    aws_access_key,
                    aws_secret_key
                )
                
                if "error" in response:
                    assistant_reply = f"❗ Error: {response['error']}"
                else:
                    assistant_reply = response.get("reply", "Sorry, no response received.")
                
                placeholder.write(assistant_reply)
            
            # Add assistant response and refresh
            st.session_state["messages"].append({"role": "assistant", "content": assistant_reply})
            st.rerun()
    
    with tab2:
        # Monitoring dashboard
        render_metrics_dashboard()
        
        # Manual refresh button
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        # Auto-refresh info
        st.caption("💡 Data refreshes automatically when you send new messages or manually refresh")


def main():
    """
    Main application entry point.
    
    Handles session initialization, authentication state management,
    and routing between login and main application interfaces.
    
    Returns:
        None
    """
    init_session_state()
    
    # Check authentication status
    if not st.session_state["authenticated"]:
        render_login_page()
    else:
        # Verify token validity
        if not verify_token():
            st.session_state["authenticated"] = False
            st.session_state["token"] = None
            st.error("Session expired, please login again")
            st.rerun()
        else:
            render_main_app()


if __name__ == "__main__":
    main() 
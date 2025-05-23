import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import chatbot
from botocore.exceptions import NoCredentialsError, EndpointConnectionError

@pytest.fixture(autouse=True)
def setup_session_state():
    """
    Automatically clear and initialize the Streamlit session state before each test.
    Ensures a clean test environment with a fresh conversation history.
    """
    st.session_state.clear()
    chatbot.initialize_session_state()

def test_initialize_session_state():
    """
    Test that `initialize_session_state()` correctly sets up an empty conversation list.
    """
    assert "conversation" in st.session_state
    assert isinstance(st.session_state.conversation, list)

def test_initialize_and_display(monkeypatch):
    """
    Test that session state initializes and display_title_and_description renders without error.
    """
    chatbot.initialize_session_state()
    assert isinstance(st.session_state.conversation, list)
    monkeypatch.setattr(st, "title", lambda x: None)
    monkeypatch.setattr(st, "markdown", lambda x: None)
    chatbot.display_title_and_description()

def test_chat_key_error_handling():
    """
    Simulate a malformed Bedrock response and verify error handling in the `chat()` function.
    """
    with patch("chatbot.get_bedrock_client") as mock_client:
        mock = MagicMock()
        mock.converse.return_value = {"output": {}}  # Missing keys
        mock_client.return_value = mock
        response = chatbot.chat("Trigger KeyError")
        assert "Unexpected Error" in response

def test_display_conversation_history(monkeypatch):
    """
    Test `display_conversation_history()` with valid and invalid message roles.
    """
    st.session_state.conversation = [
        {"role": "user", "content": [{"text": "Hi"}]},
        {"role": "assistant", "content": [{"text": "Hello!"}]},
        {"role": "unknown", "content": [{"text": "???"}]}  # Triggers warning
    ]
    monkeypatch.setattr(st, "chat_message", lambda role: MagicMock(markdown=lambda text: None))
    chatbot.display_conversation_history()

def test_handle_user_input(monkeypatch):
    """
    Test `handle_user_input()` by mocking input and verifying it triggers a reply rendering.
    """
    monkeypatch.setattr(chatbot, "chat", lambda x: "Mock reply")
    monkeypatch.setattr(st, "chat_input", lambda x=None: "Hello")
    monkeypatch.setattr(st, "chat_message", lambda role: MagicMock(markdown=lambda text: None))
    chatbot.handle_user_input()

def test_bedrock_client_no_credentials():
    """
    Simulate AWS credential error when calling `get_bedrock_client()`.
    """
    with patch("chatbot.boto3.client", side_effect=NoCredentialsError()):
        with pytest.raises(NoCredentialsError):
            chatbot.get_bedrock_client()

def test_bedrock_client_endpoint_error():
    """
    Simulate a network error and confirm `EndpointConnectionError` is handled.
    """
    with patch("chatbot.boto3.client", side_effect=EndpointConnectionError(endpoint_url="https://example.com")):
        with pytest.raises(EndpointConnectionError):
            chatbot.get_bedrock_client()

def test_bedrock_client_generic_exception():
    """
    Simulate a generic exception in `get_bedrock_client()` to ensure fallback is tested.
    """
    with patch("chatbot.boto3.client", side_effect=Exception("Generic failure")):
        with pytest.raises(Exception):
            chatbot.get_bedrock_client()

def test_chat_appends_user_input():
    """
    Test that the chat function adds user and assistant messages to session state.
    """
    with patch("chatbot.get_bedrock_client") as mock_client:
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.return_value = {
            "output": {
                "message": {
                    "content": [{"text": "Hello!"}]
                }
            }
        }
        result = chatbot.chat("Hi")
        assert result == "Hello!"
        assert st.session_state.conversation[-2]["role"] == "user"
        assert st.session_state.conversation[-1]["role"] == "assistant"

def test_chat_empty_input():
    """
    Ensure `chat()` returns a warning when user input is empty or only spaces.
    """
    result = chatbot.chat("   ")
    assert "Input cannot be empty" in result

def test_chat_invalid_response_format():
    """
    Simulate an invalid Bedrock response format and ensure the error is handled.
    """
    with patch("chatbot.get_bedrock_client") as mock_client:
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        mock_bedrock.converse.return_value = {
            "output": {
                "message": {
                    "content": []  # Invalid: no first element
                }
            }
        }
        response = chatbot.chat("Test")
        assert "Unexpected Error" in response
        assert "Traceback" in response

def test_chat_bedrock_exception():
    """
    Simulate a complete failure during `chat()` to test outer exception block.
    """
    with patch("chatbot.get_bedrock_client") as mock_client:
        mock_client.side_effect = Exception("Simulated failure")
        response = chatbot.chat("Test")
        assert "Unexpected Error" in response

def test_main_handles_handle_user_input_failure(monkeypatch):
    """
    Force `handle_user_input()` to raise an exception and ensure `main()` handles it gracefully.
    """
    monkeypatch.setattr(st, "error", lambda msg: None)
    monkeypatch.setattr(st, "text", lambda msg: None)
    monkeypatch.setattr(st, "code", lambda msg, language="": None)
    monkeypatch.setattr(chatbot, "handle_user_input", lambda: (_ for _ in ()).throw(Exception("Mock failure")))
    chatbot.main()

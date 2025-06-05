import os
import logging
from datetime import datetime

import streamlit as st
from metrics import record_invocation 
from bedrock_api import query_bedrock
import logging_config

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Starting Bedrock Chatbot Streamlit app")

def set_aws_credentials_in_env(access_key: str, secret_key: str) -> None:
    """
    Store AWS credentials in environment variables so that query_bedrock()
    picks them up at call time.
    """
    os.environ["AWS_ACCESS_KEY_ID"] = access_key
    os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key
    # Ensure no stale session token is present
    os.environ.pop("AWS_SESSION_TOKEN", None)


def initialize_chat_history() -> None:
    """
    Initialize Streamlit session state with an empty list so that
    the first message is always from the user.
    """
    if "messages" not in st.session_state:
        st.session_state["messages"] = []


def render_chat_history() -> None:
    """
    Render every message in st.session_state["messages"] as a chat bubble.
    """
    for msg in st.session_state["messages"]:
        st.chat_message(msg["role"]).write(msg["content"])


def handle_user_input(aws_access_key: str, aws_secret_key: str) -> None:
    """
    Wait for new user input. When detected:
      1) Validate AWS credentials.
      2) Write credentials to os.environ.
      3) Append user message to history.
      4) Call query_bedrock() with the full history.
      5) Append the assistant's reply and rerun to update UI.

    Args:
        aws_access_key: AWS_ACCESS_KEY_ID from the sidebar.
        aws_secret_key: AWS_SECRET_ACCESS_KEY from the sidebar.
    """
    prompt = st.chat_input("Type your message and press Enter…")
    if not prompt:
        return  # No input yet

    # Validate credentials
    if not aws_access_key or not aws_secret_key:
        st.sidebar.error("🔒 AWS credentials are required to send a message.")
        st.stop()

    # Set them in the environment
    set_aws_credentials_in_env(aws_access_key, aws_secret_key)

    # Append the new user message
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Call Bedrock with the full history
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.write("⏳ Thinking…")

        start_time = datetime.now()
        success = False
        try:
            assistant_reply = query_bedrock(st.session_state["messages"])
            success = True
        except Exception as e:
            logger.error(f"Error calling Bedrock: {e}", exc_info=True)
            assistant_reply = "❗ Sorry, I encountered an error."
        end_time = datetime.now()

        # Record metrics here
        latency_ms = (end_time - start_time).total_seconds() * 1000.0
        record_invocation(latency_ms=latency_ms, success=success)

        placeholder.write(assistant_reply)

    # Append assistant's reply to history and rerun
    st.session_state["messages"].append({"role": "assistant", "content": assistant_reply})
    st.rerun()


def main() -> None:
    """
    Streamlit entry point. Sets up the page layout, sidebar, and chat canvas.
    """
    # Set page configuration
    st.set_page_config(
        page_title="💬 Bedrock Chatbot",
        page_icon="🤖",
        layout="wide"
    )

    # ───── Sidebar ─────
    with st.sidebar:
        st.sidebar.header("🔑 AWS Credentials")
        aws_access_key = st.sidebar.text_input(
            "Access Key ID", key="aws_access_key", type="password"
        )
        aws_secret_key = st.sidebar.text_input(
            "Secret Access Key", key="aws_secret_key", type="password"
        )

        st.sidebar.markdown("---")
        st.sidebar.info(
            """
            ▶ Enter your **AWS Access Key ID** and **Secret Access Key** here 
            so the app can securely talk to Amazon Bedrock on your behalf.

            ▶ We only use these credentials **for the current session**— 
            they are never written to disk or shared with anyone.

            ▶ As soon as you close this browser tab, your keys are forgotten.
            """
        )

    # ───── Main Chat Area ─────
    # Page title and subtitle
    st.markdown("# 💬 Bedrock Chatbot")
    st.markdown(
        "Welcome! This chat window uses Amazon Bedrock (Claude) under the hood. "
        "Type a message below to get started."
    )
    st.markdown("---")

    # Initialize and render chat history
    initialize_chat_history()
    render_chat_history()

    # Handle new user input and generate a response
    handle_user_input(aws_access_key, aws_secret_key)


if __name__ == "__main__":
    main()

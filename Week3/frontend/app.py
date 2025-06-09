import os
import hashlib
import streamlit as st
import requests

# ─── Constants ─────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000/chat"


def get_user_id(access_key: str) -> str:
    """
    Compute a stable user identifier by hashing the AWS access key.

    :param access_key: AWS Access Key ID
    :return: Hex-encoded SHA-256 hash as user_id
    """
    return hashlib.sha256(access_key.encode("utf-8")).hexdigest()


def login_sidebar() -> None:
    """
    Render the sidebar login form for AWS credentials. On successful
    authentication, store credentials and flag in st.session_state.
    """
    st.sidebar.header("User Authentication")
    access_key = st.sidebar.text_input("AWS Access Key ID", type="password")
    secret_key = st.sidebar.text_input("AWS Secret Access Key", type="password")
    region = st.sidebar.text_input(
        "AWS Region", value=os.getenv("AWS_REGION", "us-east-1")
    )

    if st.sidebar.button("Log In"):
        # Prepare a test ping to validate credentials
        payload = {
            "user_id": get_user_id(access_key),
            "access_key": access_key,
            "secret_key": secret_key,
            "region": region,
            "messages": [
                {"role": "system", "content": "Authenticate"},
                {"role": "user",   "content": "Ping"}
            ]
        }
        try:
            resp = requests.post(API_URL, json=payload)
            if resp.status_code == 200:
                # Store credentials for use by chat
                st.session_state.authenticated = True
                st.session_state.access_key = access_key
                st.session_state.secret_key = secret_key
                st.session_state.region = region
                st.success("Logged in successfully")
            else:
                st.error("Authentication failed: check your keys")
        except requests.exceptions.RequestException:
            st.error("Cannot reach chat service")


def send_message_and_get_reply(user_text: str) -> str:
    """
    Send the full conversation (including the new user_text) to the chat API,
    and return the assistant's reply.

    :param user_text: The new user message
    :return: Assistant reply text
    """
    # Append the new user message
    st.session_state.messages.append({"role": "user", "content": user_text})

    # Build payload including all messages so far
    payload = {
        "user_id": get_user_id(st.session_state.access_key),
        "access_key": st.session_state.access_key,
        "secret_key": st.session_state.secret_key,
        "region": st.session_state.region,
        "messages": st.session_state.messages,
    }

    # Call backend
    resp = requests.post(API_URL, json=payload)
    resp.raise_for_status()
    reply = resp.json().get("response", "")

    return reply


def render_chat_interface() -> None:
    """
    Display the chat messages and handle new user inputs.
    """
    # Initialize message history if first load
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Welcome!"}]

    # Render all existing messages
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Handle user input
    if user_text := st.chat_input("Your message…"):
        # Render user bubble immediately
        st.chat_message("user").write(user_text)

        # Send to backend and get reply
        try:
            reply = send_message_and_get_reply(user_text)
        except Exception as e:
            st.error(f"Chat service error: {e}")
            return

        # Render assistant response
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)


def main() -> None:
    """
    Main entry point: set up page, run login sidebar and chat interface.
    """
    # Page config and title
    st.set_page_config(page_title="Enterprise Chat", page_icon="💼")
    st.title("Enterprise Chat Application")

    # Sidebar login
    login_sidebar()

    # Show chat only when authenticated
    if st.session_state.get("authenticated"):
        render_chat_interface()
    else:
        st.info("Please log in with AWS credentials in the sidebar.")


if __name__ == "__main__":
    main()

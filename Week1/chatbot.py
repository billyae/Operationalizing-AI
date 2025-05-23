import streamlit as st
import boto3
import traceback
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, EndpointConnectionError

# === CONFIGURATION ===
REGION = "us-east-1"
MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

def main():
    """Main entry point for the Streamlit Bedrock Chat App."""
    try:
        initialize_session_state()
        display_title_and_description()
        display_conversation_history()
        handle_user_input()
    except Exception as e:
        st.error(f"❌ An unexpected error occurred:\n\n```{str(e)}```")
        st.text("Traceback:")
        st.code(traceback.format_exc(), language="python")

@st.cache_resource
def get_bedrock_client():
    """
    Create and cache the AWS Bedrock runtime client.

    Returns:
        boto3.Client: The Bedrock runtime client.
    """
    try:
        return boto3.client("bedrock-runtime", region_name=REGION)
    except NoCredentialsError:
        st.error("❌ AWS credentials not found. Please set them in your environment or use `aws configure`.")
        raise
    except EndpointConnectionError:
        st.error("❌ Could not connect to Bedrock endpoint. Check your AWS region and network.")
        raise
    except Exception as e:
        st.error(f"❌ Failed to initialize Bedrock client: {str(e)}")
        raise

def initialize_session_state():
    """Initialize Streamlit session state for conversation if not already set."""
    if "conversation" not in st.session_state:
        st.session_state.conversation = []

def chat(user_input: str) -> str:
    """
    Send user input to the Bedrock model and get a response.

    Args:
        user_input (str): The user's message.

    Returns:
        str: Assistant's reply or error message.
    """
    if not user_input.strip():
        return "⚠️ Input cannot be empty."

    st.session_state.conversation.append({
        "role": "user",
        "content": [{"text": user_input}]
    })

    try:
        client = get_bedrock_client()
        response = client.converse(
            modelId=MODEL_ID,
            messages=st.session_state.conversation,
            inferenceConfig={"maxTokens": 150, "temperature": 0.7, "topP": 0.9}
        )

        # Validate response format
        try:
            reply = response["output"]["message"]["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            st.error("❌ Unexpected response format from Bedrock.")
            st.text("Full response:")
            st.json(response)
            raise e

        st.session_state.conversation.append({
            "role": "assistant",
            "content": [{"text": reply}]
        })
        return reply

    except (BotoCoreError, ClientError) as e:
        return f"❌ [Bedrock API Error] {str(e)}"
    except Exception as e:
        return f"❌ [Unexpected Error] {str(e)}\n\nTraceback:\n{traceback.format_exc()}"

def display_title_and_description():
    """Display the app title and description."""
    st.title("💬 Conversational AI Assistant")
    st.markdown("Chat with a helpful assistant powered by Amazon Bedrock.")

def display_conversation_history():
    """Render all conversation history."""
    for msg in st.session_state.conversation:
        role = "🧑 You" if msg["role"] == "user" else "🤖 Assistant"
        try:
            st.chat_message(role).markdown(msg["content"][0]["text"])
        except Exception:
            st.warning(f"⚠️ Skipped malformed message: {msg}")

def handle_user_input():
    """Handle user input and update the chat interface."""
    if prompt := st.chat_input("Type your message here..."):
        st.chat_message("🧑 You").markdown(prompt)
        reply = chat(prompt)
        st.chat_message("🤖 Assistant").markdown(reply)

# Run the app
if __name__ == "__main__":
    main()

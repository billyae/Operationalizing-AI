# Conversational AI Assistant using Amazon Bedrock

This is a lightweight web-based chatbot interface built with **Streamlit** and powered by **Amazon Bedrock**, using models like **Anthropic Claude 3 Sonnet**. It enables real-time, multi-turn conversations via a clean, interactive UI.

---

## Features

- Real-time interaction with Anthropic Claude 3 via Bedrock
- Session-based memory and context management using Streamlit's session state
- Conprehensive error handling for missing credentials, format issues, and API exceptions
- Minimal and intuitive Streamlit UI

---

## Prerequisites

- Python 3.8+
- Access to Amazon Bedrock (with model permissions)
- AWS credentials configured

---

## Run the Code

```bash

# Install dependencies
pip install -r requirements.txt

# Add AWS Credentials

# For windows:   
$env:AWS_ACCESS_KEY_ID = "your-access-key-id"
$env:AWS_SECRET_ACCESS_KEY = "your-secret-access-key"

# For Linux/Mac:   
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"

# Run this app
streamlit run chatbot.py

# Test this app
pytest test-chatbot.py --cov=chatbot --cov-report=term-missing

```

## API Patterns & Usage

This project uses the [`converse()`](https://docs.aws.amazon.com/bedrock/latest/userguide/model-apis.html) method of the Amazon Bedrock Runtime API to enable interactive, multi-turn conversations with Claude 3.

### Request Structure

The request to `client.converse(...)` follows this structure:

```python
response = client.converse(
    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
    messages=[
        {"role": "user", "content": [{"text": "Hello"}]},
        {"role": "assistant", "content": [{"text": "Hi! How can I help you?"}]}
    ],
    inferenceConfig={
        "maxTokens": 150,
        "temperature": 0.7,
        "topP": 0.9
    }
)
```
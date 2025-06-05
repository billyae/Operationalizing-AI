# Bedrock Chatbot Pipeline

A Streamlit-based chatbot that uses Amazon Bedrock (Anthropic Claude) as its LLM backend. It includes a chat interface, a simple metrics recorder, and a real‐time monitoring dashboard.

## Features

**Chat Interface (chat_app.py):**
- Streamlit UI for user messages.   
- Sends prompts to Bedrock via bedrock_api.py.   
- Displays model responses and tracks each invocation’s latency and success status.

**Metrics Module (metrics.py):**
- Records invocation latency (in milliseconds) and success/failure.
- Persists metrics in a local SQLite database (metrics.db).

**Logging Configuration (logging_config.py):**
- Sets up a rotating file handler under logs/bedrock_chatbot.log.
- Logs INFO-level (and above) messages with timestamps and module names.

**Monitoring Dashboard (dashboard.py):**
- Streamlit dashboard that tails the application log file in real time.
- Reads metrics from metrics.db to plot invocation latency and success rate.

## Prerequisites

- Python 3.8+

- AWS credentials with Bedrock access (set via environment variables or passed directly in the UI).

## Configuration

### AWS Credentials

Either set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY as environment variables, or enter them directly in the Streamlit sidebar when running chat_app.py.

### Logging Directory 

By default, logs/bedrock_chatbot.log is created under a logs/ folder. Ensure the application has write access.

## Usage

### Run the Chatbot

`streamlit run chat_app.py`

- In the sidebar, paste your AWS credentials.

- Type messages into the chat box; responses come from Bedrock.

### Run the Monitoring Dashboard

`streamlit run dashboard.py`

- Displays a live tail of logs/bedrock_chatbot.log.

- Plots invocation latency and success/failure from metrics.db.

## Project Structure

├── chat_app.py            # Streamlit chat UI  
├── bedrock_api.py         # Wrapper for Amazon Bedrock calls  
├── metrics.py             # Records invocation metrics to SQLite   
├── logging_config.py      # Rotating-file logging setup     
├── requirements.txt       # Python dependencies       
├── monitoring/     
    └──  dashboard.py      # Streamlit dashboard for logs & metrics   
├── metrics/    
    └── metrics.db         # SQLite database (created at runtime)     
└── logs/  
    └── bedrock_chatbot.log # Rotating log file  


## License

This project is provided “as-is” under the MIT License.




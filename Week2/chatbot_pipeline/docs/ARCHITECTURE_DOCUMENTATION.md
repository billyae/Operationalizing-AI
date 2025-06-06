# Bedrock Chatbot Architecture

## 1. Overview
A Streamlit-based chat application that routes user messages to Amazon Bedrock (Claude) and displays responses in real time. The system records invocation metrics in SQLite and writes logs to rotating files. A separate Streamlit dashboard visualizes these metrics and recent log entries.

## 2. Components

### 2.1 Frontend (Streamlit Chat App)
- **File:** `chat_app.py`
- **Responsibilities:**
  - Render chat UI and sidebar for AWS credentials.
  - Collect user input and append to `st.session_state["messages"]`.
  - Call Bedrock via `query_bedrock()` and display assistant reply.
  - Record metrics (latency, success) to SQLite using `record_invocation()`.

### 2.2 Bedrock API Wrapper
- **File:** `bedrock_api.py`
- **Responsibilities:**
  - Load AWS credentials from environment.
  - Build payload in Anthropic chat format.
  - Invoke `bedrock-runtime` client (Claude model).
  - Parse and return assistant response.
  - Retry on `ClientError` up to 3 times.

### 2.3 Metrics & Database
- **File:** `metrics.py`
- **Responsibilities:**
  - Ensure `metrics/metrics.db` directory exists.
  - Create and manage `invocations` table.
  - Insert invocation records (timestamp, latency_ms, success).
  - Fetch all records for reporting.

### 2.4 Logging Configuration
- **File:** `logging_config.py`
- **Responsibilities:**
  - Ensure `logs/` directory exists.
  - Configure a rotating file handler (`bedrock_chatbot.log`, 5 MB, 3 backups).
  - Configure console handler (warnings and above).
  - Provide named loggers via `get_logger()`.

### 2.5 Monitoring Dashboard
- **File:** `dashboard.py`
- **Responsibilities:**
  - Load metrics from SQLite and aggregate per-minute stats.
  - Tail the last 20 lines from `logs/bedrock_chatbot.log`.
  - Render real-time charts: requests/minute, average latency, error rate.
  - Display raw invocations in an interactive table.

## 3. Data Flow

1. **User → Streamlit Chat App**  
   - User enters AWS Access Key and Secret Key in sidebar.  
   - User types a message in the chat input.

2. **Chat App → Bedrock API**  
   - Credentials are set to `os.environ`.  
   - `query_bedrock()` is called with chat history.  

3. **Bedrock API → Amazon Bedrock**  
   - Payload is formatted and sent to Claude model.  
   - Response is parsed and returned to chat app.

4. **Chat App → Metrics Logger**  
   - Compute latency (ms) and success flag.  
   - Call `record_invocation()` to insert a new row into SQLite.

5. **Chat App → UI**  
   - Display assistant’s reply in chat.

6. **Dashboard → SQLite & Logs**  
   - Periodically read `metrics.db` for aggregated stats.  
   - Tail `bedrock_chatbot.log` for recent log entries.  
   - Update charts and tables in Streamlit.

## 4. Directory Structure

├── chat_app.py    # Streamlit chat UI    
├── bedrock_api.py    # Wrapper for Amazon Bedrock calls   
├── metrics.py     # Records invocation metrics to SQLite     
├── logging_config.py    # Rotating-file logging setup    
├── requirements.txt    # Python dependencies    
├── monitoring/    
│ └── dashboard.py   # Streamlit dashboard for logs & metrics    
├── metrics/    
│ └── metrics.db    # SQLite database (created at runtime)     
└── logs/    
│ └── bedrock_chatbot.log    # Rotating log file     
└── docs/    
│ └── ARCHITECTURE_DOCUMENT.md    # Architecture document file      
│ └── TECHNICAL_WRITEUP.md    # Technical write up file  

## 5. Deployment

- **Environment Variables:**  
  - AWS_ACCESS_KEY_ID  
  - AWS_SECRET_ACCESS_KEY  
  - (Optional) AWS_SESSION_TOKEN, AWS_REGION  

- **Steps:**  
  1. Install dependencies:  
     ```bash
     pip install -r requirements.txt
     ```  
  2. Run the chat app:  
     ```bash
     streamlit run chat_app.py
     ```  
  3. Run the monitoring dashboard in a separate terminal:  
     ```bash
     streamlit run dashboard.py
     ```

## 6. Tech Stack

- **Frontend:** Streamlit  
- **Backend API:** Boto3 (`bedrock-runtime`)  
- **Database:** SQLite (via `sqlite3`)  
- **Logging:** Python `logging`, `RotatingFileHandler`  
- **Runtime:** Python 3.8+  


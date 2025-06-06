# Technical Writeup

## 1. Chat Application (`chat_app.py`)
- **Imports:** `streamlit`, `time`, `os`, `logging`, `bedrock_api.query_bedrock`, `metrics.record_invocation`.
- **Sidebar:**  
  - Two `st.text_input` fields for AWS Access Key ID and Secret Key.  
  - On change, set `os.environ["AWS_ACCESS_KEY_ID"]` and `os.environ["AWS_SECRET_ACCESS_KEY"]`.
- **Session State:**  
  - Initialize `st.session_state["messages"]` with a single assistant greeting if not present.  
  - Each message is a dict `{ "role": "user"|"assistant", "content": <text> }`.
- **Chat Loop:**  
  1. Render existing messages via `st.chat_message(msg["role"]).write(msg["content"])`.  
  2. When user enters text in `st.chat_input()`:  
     - Append `{"role":"user","content": prompt}` to `st.session_state["messages"]`.  
     - Call `query_bedrock(st.session_state["messages"])` and measure latency with `time.time()`.  
     - Append assistant response to session state.  
     - Call `record_invocation(latency_ms, success_flag)` regardless of errors.  

## 2. Bedrock API Wrapper (`bedrock_api.py`)
- **Imports:** `boto3`, `botocore.exceptions.ClientError`, `os`, `logging`.
- **`get_bedrock_client()`**:  
  - Reads `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optional `AWS_SESSION_TOKEN` / `AWS_REGION` from `os.environ`.  
  - Returns `boto3.client("bedrock-runtime")`.
- **`query_bedrock(messages: List[Dict]) -> str`**:  
  1. Format payload as Anthropic chat:  
     ```json
     {
       "modelId": "anthropic.claude-v2",
       "messages": [
         {"role": "user", "content": "<concatenated history>"}
       ]
     }
     ```  
  2. Retry up to 3 times on `ClientError` (exponential backoff).  
  3. Parse `response["completions"][0]["data"]["content"]` and return as string.  
  4. Log errors via `logging.getLogger("bedrock").error(...)`.

## 3. Metrics (`metrics.py`)
- **Imports:** `sqlite3`, `os`, `datetime`.
- **Database Initialization:**  
  - Ensure `metrics/` directory exists.  
  - Connect to `metrics/metrics.db`.  
  - Create table `invocations (timestamp TEXT, latency_ms INTEGER, success INTEGER)` if not exists.
- **`record_invocation(latency_ms: int, success: bool) -> None`**:  
  - `timestamp = datetime.utcnow().isoformat()`.  
  - Insert `(timestamp, latency_ms, int(success))` into `invocations`.  
- **`fetch_invocations() -> List[Tuple]`**:  
  - Return all rows: `SELECT * FROM invocations ORDER BY timestamp ASC`.

## 4. Logging Configuration (`logging_config.py`)
- **Imports:** `logging`, `logging.handlers`, `os`.
- **Setup:**  
  1. Ensure `logs/` directory exists.  
  2. Configure a `RotatingFileHandler` writing to `logs/bedrock_chatbot.log` (5 MB max, 3 backups).  
  3. Configure a `StreamHandler` at `WARNING` level.  
  4. Use format: `'%(asctime)s [%(levelname)s] %(name)s: %(message)s'`.
- **`get_logger(name: str) -> logging.Logger`**:  
  - Returns a named logger with both handlers attached.

## 5. Monitoring Dashboard (`monitoring/dashboard.py`)
- **Imports:** `streamlit`, `pandas`, `sqlite3`, `time`, `os`.
- **Metrics Loading:**  
  1. Connect to `metrics/metrics.db` and read `invocations` into a DataFrame.  
  2. Parse `timestamp` column to `datetime`, floor to the minute:  
     ```python
     df["minute"] = df["timestamp"].dt.floor("min")
     stats = df.groupby("minute").agg(
       requests=("latency_ms", "count"),
       avg_latency=("latency_ms", "mean"),
       error_rate=("success", lambda s: 1 - s.mean())
     )
     ```
- **Charts:**  
  - Use `st.line_chart` for `requests`, `avg_latency`, and `error_rate` over time.
- **Raw Table:**  
  - Display full `invocations` DataFrame via `st.dataframe` (sorted by timestamp).
- **Log Tail:**  
  1. Read last 20 lines from `logs/bedrock_chatbot.log`.  
  2. Display via `st.text_area` with `height=300`.
- **Auto-Refresh:**  
  - Place `st.experimental_rerun()` with `time.sleep(60)` to update every minute (optional).

## 6. Dependencies (`requirements.txt`)

- streamlit
- boto3
- pandas

## 7. Runtime & Deployment
1. **Install:**  
   
   ```pip install -r requirements.txt```

2. **Set AWS Credentials:** 

    Enter keys in chat UI sidebar (stored in memory only).

3. **Run Chat App:**   
    `streamlit run chat_app.py`

4. **Run Dashboard (separate terminal):**     
    `streamlit run monitoring/dashboard.py`
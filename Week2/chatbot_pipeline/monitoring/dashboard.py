# monitoring/dashboard.py
import streamlit as st
import pandas as pd
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "../metrics/metrics.db")

@st.cache_data(ttl=30)
def load_metrics():
    """
    Returns a DataFrame containing all rows from the invocations table.
    """
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["id", "timestamp", "latency_ms", "success"])

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    df = pd.read_sql_query("SELECT * FROM invocations ORDER BY id ASC", conn, parse_dates=["timestamp"])
    conn.close()
    return df

def tail_log(n=20):
    """
    Return last n lines from logs/bedrock_chatbot.log
    """
    log_file = os.path.join(os.path.dirname(__file__), "../logs/bedrock_chatbot.log")
    if not os.path.exists(log_file):
        return ["(no log file found)"]
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines[-n:]

def main():
    st.set_page_config(page_title="Bedrock Chatbot Metrics", layout="wide")
    st.title("📊 Bedrock Chatbot Monitoring Dashboard")

    st.sidebar.header("Log Tail (last 20 lines):")
    for line in tail_log(20):
        st.sidebar.text(line.rstrip())

    df = load_metrics()
    if df.empty:
        st.warning("No metrics yet. Run the chatbot (`python main.py`) and come back.")
        return

    # Convert timestamp column to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Compute some aggregates
    df["minute"] = df["timestamp"].dt.floor("T")
    per_minute = df.groupby("minute").agg(
        total_requests=("id", "count"),
        avg_latency_ms=("latency_ms", "mean"),
        error_rate=("success", lambda s: 1.0 - s.mean())
    ).reset_index()

    st.subheader("Requests per Minute")
    st.line_chart(per_minute.set_index("minute")["total_requests"])

    st.subheader("Average Latency (ms) per Minute")
    st.line_chart(per_minute.set_index("minute")["avg_latency_ms"])

    st.subheader("Error Rate per Minute")
    st.line_chart(per_minute.set_index("minute")["error_rate"])

    st.subheader("Raw Invocations Table")
    st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)

if __name__ == "__main__":
    main()

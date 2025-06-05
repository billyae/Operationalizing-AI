import streamlit as st
import pandas as pd
import sqlite3
import os
import logging
import time

logger = logging.getLogger(__name__)

# Path to the SQLite database storing invocation metrics
DB_PATH = os.path.join(os.path.dirname(__file__), "../metrics/metrics.db")


def load_metrics():
    """
    Load invocation metrics from the SQLite database.

    Returns:
        pandas.DataFrame: A DataFrame containing all rows from the 'invocations' table,
                          with columns ['id', 'timestamp', 'latency_ms', 'success'].
                          If the DB does not exist, returns an empty DataFrame
                          with those columns.
    """
    if not os.path.exists(DB_PATH):
        # If the database file does not exist yet, return an empty DataFrame
        return pd.DataFrame(columns=["id", "timestamp", "latency_ms", "success"])

    # Connect to the SQLite database (allowing multi-threaded reads)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)

    # Read the entire 'invocations' table, parsing 'timestamp' into datetime objects
    df = pd.read_sql_query(
        "SELECT * FROM invocations ORDER BY id ASC",
        conn,
        parse_dates=["timestamp"],
    )
    conn.close()
    return df


def tail_log(n=20):
    """
    Read the last n lines from the Bedrock Chatbot log file.

    Args:
        n (int): Number of lines from the end of the log to return (default: 20).

    Returns:
        list[str]: A list of the last n log lines. If the log file does not exist,
                   returns a single-element list indicating no log file found.
    """
    log_file = os.path.join(os.path.dirname(__file__), "../logs/bedrock_chatbot.log")
    if not os.path.exists(log_file):
        # If the log file doesn't exist, indicate that in the output
        return ["(no log file found)"]

    # Read all lines from the log file and return the last n lines
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines[-n:]


def main():
    """
    Entry point for the Streamlit dashboard.

    Sets up the dashboard layout, continuously reads metrics & logs every second,
    computes per-minute aggregates, and updates charts/tables in real-time.
    """
    # Configure the Streamlit page (must be called before any other Streamlit commands)
    st.set_page_config(page_title="Bedrock Chatbot Metrics", layout="wide")
    st.title("📊 Bedrock Chatbot Monitoring Dashboard")

    # Create Streamlit placeholders that we will update inside the loop
    sidebar_placeholder = st.sidebar.empty()
    chart_requests_placeholder = st.empty()
    chart_latency_placeholder = st.empty()
    chart_error_placeholder = st.empty()
    table_placeholder = st.empty()

    # Infinite loop to refresh metrics and logs every second
    while True:
        # ─── Sidebar: Display the last 20 lines of the chatbot log ─────────────────
        with sidebar_placeholder.container():
            st.header("Log Tail (last 20 lines):")
            for line in tail_log(20):
                st.text(line.rstrip())

        # ─── Load metrics from the SQLite database ─────────────────────────────────
        df = load_metrics()
        if df.empty:
            # If we have no data yet, prompt the user to run the chatbot
            st.warning("No metrics yet. Run the chatbot (`python main.py`) and come back.")
            time.sleep(2)
            continue  # Retry after a short pause

        # Ensure 'timestamp' column is of datetime type for grouping
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Add a 'minute' column by flooring timestamps to the nearest minute
        df["minute"] = df["timestamp"].dt.floor("min")

        # Compute per-minute aggregates:
        #   - total_requests: number of invocations in that minute
        #   - avg_latency_ms: average latency in milliseconds
        #   - error_rate: fraction of failed invocations
        per_minute = (
            df.groupby("minute")
            .agg(
                total_requests=("id", "count"),
                avg_latency_ms=("latency_ms", "mean"),
                error_rate=("success", lambda s: 1.0 - s.mean()),
            )
            .reset_index()
        )

        # ─── Charts ────────────────────────────────────────────────────────────────

        # Requests per Minute chart
        with chart_requests_placeholder.container():
            st.subheader("Requests per Minute")
            st.line_chart(per_minute.set_index("minute")["total_requests"])

        # Average Latency per Minute chart
        with chart_latency_placeholder.container():
            st.subheader("Average Latency (ms) per Minute")
            st.line_chart(per_minute.set_index("minute")["avg_latency_ms"])

        # Error Rate per Minute chart
        with chart_error_placeholder.container():
            st.subheader("Error Rate per Minute")
            st.line_chart(per_minute.set_index("minute")["error_rate"])

        # ─── Raw Invocations Table ────────────────────────────────────────────────
        with table_placeholder.container():
            st.subheader("Raw Invocations Table")
            # Sort invocations by timestamp descending, then display in an interactive table
            st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)

        # ─── Pause briefly before the next refresh ─────────────────────────────────
        time.sleep(1)


# If this script is run directly, invoke main()
if __name__ == "__main__":
    main()

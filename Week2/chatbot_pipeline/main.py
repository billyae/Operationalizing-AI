# main.py
import time
import logging
from metrics import record_invocation
from bedrock_api import query_bedrock

logger = logging.getLogger(__name__)

def chat_loop():
    """
    A simple loop that:
    1) Prompts the user for input.
    2) Times how long query_bedrock takes.
    3) Logs success/failure and latency.
    4) Stores metrics in SQLite.
    5) Prints the model’s answer.
    """
    print("=== Welcome to Bedrock Chatbot ===")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if len(user_input) == 0:
            continue

        logger.info(f"User prompt: {user_input!r}")
        start_ts = time.time()
        success = False
        answer = ""
        try:
            answer = query_bedrock(user_input)
            success = True
        except Exception as e:
            logger.error(f"Final failure calling Bedrock: {e}", exc_info=True)
            answer = "⚠️ Sorry, I couldn’t process that request due to an error."
        end_ts = time.time()

        latency_ms = (end_ts - start_ts) * 1000.0
        record_invocation(latency_ms=latency_ms, success=success)

        if success:
            logger.info(f"Bedrock response ({latency_ms:.1f} ms): {answer!r}")
            print(f"Bot: {answer}\n")
        else:
            print(f"Bot: {answer}\n")


if __name__ == "__main__":
    chat_loop()

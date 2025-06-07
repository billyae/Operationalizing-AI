import os
import pytest
import chat_app

def test_set_aws_credentials_in_env(monkeypatch):
    """
    Test that set_aws_credentials_in_env sets the environment variables
    AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, and removes AWS_SESSION_TOKEN
    if it exists.

    Args:
        monkeypatch: pytest fixture to modify environment variables.
    """
    # Set initial environment variables
    monkeypatch.setenv("AWS_SESSION_TOKEN", "tok")
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    chat_app.set_aws_credentials_in_env("KEY123", "SEC456")
    assert os.environ["AWS_ACCESS_KEY_ID"] == "KEY123"
    assert os.environ["AWS_SECRET_ACCESS_KEY"] == "SEC456"
    assert "AWS_SESSION_TOKEN" not in os.environ

def test_initialize_chat_history(monkeypatch):

    """
    Test that initialize_chat_history initializes the session state
    with an empty list if "messages" is not already set.
    If "messages" is already set, it should not change it.
    Args:
        monkeypatch: pytest fixture to modify Streamlit's session state.
    """

    dummy = type("StStub", (), {})()
    dummy.session_state = {}
    monkeypatch.setattr(chat_app, "st", dummy)

    chat_app.initialize_chat_history()
    assert dummy.session_state["messages"] == []

    dummy.session_state["messages"] = ["already"]
    chat_app.initialize_chat_history()
    assert dummy.session_state["messages"] == ["already"]

class StubSt:
    """Minimal Streamlit stub for chat_app."""
    def __init__(self, next_input=""):
        self.session_state = {}
        self._next_input = next_input
        self.bubbles = []
        self.errors = []
        self.sidebar = self
        self.page_config = {}

    # support "with st.sidebar:"
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): return False

    # sidebar API
    def header(self, txt):        self.last_header = txt
    def info(self, txt):          self.last_info = txt
    def text_input(self, *args, **kwargs): return self._next_input
    def error(self, txt):         self.errors.append(txt)   # ← ADDED

    def markdown(self, txt):       self.last_markdown = txt
    def set_page_config(self, **kw): self.page_config = kw

    # chat canvas API
    def chat_input(self, *args, **kwargs):
        """
        Simulate the chat input box. Returns the next input set in the constructor.
        """
        return self._next_input

    def chat_message(self, role):
        """
        Simulate a chat message bubble. Returns a context manager that writes
        content to the bubbles list.
        Args:
            role (str): The role of the message, e.g., "user" or "assistant".
        """
        class Bubble:
            def __init__(self, parent, role):
                self.parent, self.role = parent, role
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): return False
            def write(self, content):
                self.parent.bubbles.append((self.role, content))
        return Bubble(self, role)

    def empty(self):
        class Placeholder:
            def __init__(self, parent): self.parent = parent
            def write(self, txt):
                self.parent.bubbles.append(("placeholder", txt))
        return Placeholder(self)

    def stop(self):
        raise SystemExit()

    def rerun(self):
        raise RuntimeError("rerun called")


def test_render_chat_history(monkeypatch):
    """
    Test that render_chat_history correctly populates the chat bubbles
    with the messages from session state.
    Args:
        monkeypatch: pytest fixture to modify Streamlit's session state.
    """

    stub = StubSt()
    stub.session_state["messages"] = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    monkeypatch.setattr(chat_app, "st", stub)

    chat_app.render_chat_history()
    assert ("user", "hi") in stub.bubbles
    assert ("assistant", "hello") in stub.bubbles


def test_handle_user_input_no_prompt(monkeypatch):
    """
    Test that handle_user_input does nothing if no input is provided.
    Args:
        monkeypatch: pytest fixture to modify Streamlit's session state.
    """

    stub = StubSt(next_input="")
    monkeypatch.setattr(chat_app, "st", stub)

    # no input → returns None, no bubbles
    assert chat_app.handle_user_input("AK", "SK") is None
    assert stub.bubbles == []


def test_handle_user_input_missing_creds(monkeypatch):
    """
    Test that handle_user_input raises an error if AWS credentials are missing.
    Args:
        monkeypatch: pytest fixture to modify Streamlit's session state.
    """

    stub = StubSt(next_input="hello")
    monkeypatch.setattr(chat_app, "st", stub)

    with pytest.raises(SystemExit):
        chat_app.handle_user_input("", "")

    # now stub.errors captured the sidebar.error() call
    assert stub.errors, "Expected an error on missing creds"


def test_handle_user_input_success(monkeypatch):
    """
    Test that handle_user_input processes valid input, appends user message,
    queries Bedrock, and updates the chat history with the assistant's reply.
    Args:
        monkeypatch: pytest fixture to modify Streamlit's session state.
    """

    stub = StubSt(next_input="ping")
    stub.session_state["messages"] = []
    monkeypatch.setattr(chat_app, "st", stub)

    # stub out external calls
    monkeypatch.setattr(chat_app, "query_bedrock", lambda msgs: "pong")
    recs = []
    monkeypatch.setattr(chat_app, "record_invocation", lambda latency_ms, success: recs.append((latency_ms, success)))

    with pytest.raises(RuntimeError) as exc:
        chat_app.handle_user_input("AK", "SK")
    assert "rerun called" in str(exc.value)

    # user bubble is there
    assert ("user", "ping") in stub.bubbles

    # assistant reply "pong" could be in a placeholder bubble
    assert any(content == "pong" for _, content in stub.bubbles), stub.bubbles

    # metrics recorded with success=True
    assert recs and recs[0][1] is True


def test_main_smoke(monkeypatch):
    """
    Test that main() initializes the app, sets page config, and runs the chat loop.
    Args:
        monkeypatch: pytest fixture to modify Streamlit's session state.
    """

    stub = StubSt(next_input="foo")
    monkeypatch.setattr(chat_app, "st", stub)

    calls = {"init": False, "render": False, "handle": False}
    monkeypatch.setattr(chat_app, "initialize_chat_history", lambda: calls.update(init=True))
    monkeypatch.setattr(chat_app, "render_chat_history",     lambda: calls.update(render=True))
    def fake_handle(a, b):
        calls["handle"] = True
        raise RuntimeError("done")
    monkeypatch.setattr(chat_app, "handle_user_input", fake_handle)

    with pytest.raises(RuntimeError) as exc:
        chat_app.main()
    assert "done" in str(exc.value)

    # page config was applied
    assert stub.page_config["page_title"].startswith("💬 Bedrock Chatbot")
    # sidebar header got set
    assert hasattr(stub, "last_header")
    # our hooks ran
    assert all(calls.values())

import pytest
import requests
import streamlit as st

import frontend.app as app

class DummySession(dict):
    """
    A dummy session state that behaves like a dictionary but allows attribute-style access.
    This is used to mock Streamlit's session state in tests.
    Parameters:
        dict: A dictionary to initialize the session state with.
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"No such attribute: {name}")
    def __setattr__(self, name, value):
        self[name] = value
    def clear(self):
        super().clear()

@pytest.fixture(autouse=True)
def patch_session_state(monkeypatch):
    """
    Fixture to patch Streamlit's session state with a dummy session state.
    This allows us to test the app without needing a real Streamlit session.
    Parameters:
        monkeypatch: The pytest monkeypatch fixture to modify Streamlit's session state.
    Returns:
        st.session_state: The patched session state that behaves like a dictionary.
    """
    monkeypatch.setattr(st, "session_state", DummySession())
    return st.session_state


class DummySidebar:
    """
    A dummy sidebar that simulates Streamlit's sidebar for testing purposes.
    """
    def __init__(self, inputs, button_response):
        """
        Initializes the dummy sidebar with a list of inputs and a button response.
        Parameters:
            inputs (list): A list of inputs to simulate user input.
            button_response (bool): The response when the button is clicked.
        """
        self._inputs = iter(inputs)
        self.button_response = button_response
        self.headers = []
    def header(self, msg):
        """
        Simulates a header in the sidebar.
        Parameters:
            msg (str): The header message to display.
        """
        self.headers.append(msg)
    def text_input(self, label, type=None, value=None):
        """
        Simulates a text input in the sidebar.
        Parameters:
            label (str): The label for the text input.
            type (str): The type of the input (not used here).
            value (str): The default value for the input (not used here).
        Returns:
            str: The next input from the list of inputs.
        """
        return next(self._inputs)
    def button(self, label):
        return self.button_response

class DummyMessage:
    """
    A dummy message class to simulate Streamlit's chat message functionality for testing purposes.
    """
    def __init__(self, role, events):
        """
        Initializes the dummy message with a role and an events list.
        Parameters:
            role (str): The role of the message (e.g., "user", "assistant").
            events (list): A list to store events that occur during the test.
        """
        self.role = role
        self.events = events
    def write(self, content):
        """
        Simulates writing a message to the chat.
        Parameters:
            content (str): The content of the message to write.
        """
        self.events.append((self.role, content))

def test_get_user_id_consistency():
    """
    Test that the user ID generation is consistent for the same key.
    This ensures that the hashing function produces the same output for the same input.
    """
    key = "mykey"
    expected = app.hashlib.sha256(key.encode("utf-8")).hexdigest()
    assert app.get_user_id(key) == expected

def test_login_sidebar_success(monkeypatch):
    """
    Test the login sidebar for successful authentication.
    This simulates user input for access key, secret key, and region, and checks that the session state is updated correctly.
    Parameters:
        monkeypatch: The pytest monkeypatch fixture to modify Streamlit's sidebar and requests.
    """

    # Simulate user input in the sidebar
    sidebar = DummySidebar(inputs=["AK", "SK", "r"], button_response=True)
    monkeypatch.setattr(st, 'sidebar', sidebar)
    st.session_state.clear()
    class Resp: status_code = 200
    monkeypatch.setattr(requests, 'post', lambda url, json: Resp())
    successes = []
    monkeypatch.setattr(st, 'success', lambda msg: successes.append(msg))

    # Call the login function
    app.login_sidebar()
    assert st.session_state.authenticated
    assert st.session_state.access_key == "AK"
    assert st.session_state.secret_key == "SK"
    assert st.session_state.region == "r"
    assert successes == ["Logged in successfully"]

def test_login_sidebar_failure_and_exception(monkeypatch):
    """
    Test the login sidebar for failure cases, including authentication failure and network exceptions.
    This simulates various scenarios where the authentication fails or a network error occurs.
    Parameters:
        monkeypatch: The pytest monkeypatch fixture to modify Streamlit's sidebar and requests.
    """
    
    # authentication failure
    sidebar = DummySidebar(inputs=["A","B","R"], button_response=True)
    monkeypatch.setattr(st, 'sidebar', sidebar)
    st.session_state.clear()
    monkeypatch.setattr(requests, 'post', lambda url, json: type('R',(object,),{'status_code':400})())
    errors = []
    monkeypatch.setattr(st, 'error', lambda msg: errors.append(msg))

    # call the login function
    app.login_sidebar()
    assert errors == ["Authentication failed: check your keys"]

    # network exception
    sidebar2 = DummySidebar(inputs=["A","B","R"], button_response=True)
    monkeypatch.setattr(st, 'sidebar', sidebar2)
    st.session_state.clear()
    def ex(url, json): raise requests.exceptions.RequestException
    monkeypatch.setattr(requests, 'post', ex)
    errors2 = []
    monkeypatch.setattr(st, 'error', lambda msg: errors2.append(msg))
    app.login_sidebar()
    assert errors2 == ["Cannot reach chat service"]

def test_send_message_and_get_reply(monkeypatch):
    """
    Test sending a message and getting a reply from the chat service.
    This simulates a successful message send and checks that the session state is updated correctly.
    Parameters:
        monkeypatch: The pytest monkeypatch fixture to modify Streamlit's session state and requests.
    """

    # simulate sending a message and getting a reply
    st.session_state.clear()
    st.session_state['access_key'] = "AK"
    st.session_state['secret_key'] = "SK"
    st.session_state['region'] = "r"
    st.session_state['messages'] = []

    # mock the requests.post method to return a successful response
    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"response": "R"}
    monkeypatch.setattr(requests, 'post', lambda url, json: Resp())
    reply = app.send_message_and_get_reply("Hi")
    assert reply == "R"
    assert st.session_state['messages'][-1] == {"role":"user","content":"Hi"}

def test_render_chat_interface(monkeypatch):
    """
    Test the chat interface rendering, including the initial welcome message and user input handling.
    This simulates the chat interface and checks that messages are displayed correctly.
    Parameters:
        monkeypatch: The pytest monkeypatch fixture to modify Streamlit's session state and chat message handling.
    """

    # initial welcome message
    st.session_state.clear()
    events = []
    monkeypatch.setattr(st, 'chat_message', lambda role: DummyMessage(role, events))
    monkeypatch.setattr(st, 'chat_input', lambda prompt: None)
    app.render_chat_interface()
    assert events == [("assistant","Welcome!")]

    # with input
    st.session_state.clear()
    st.session_state['messages'] = [{"role":"assistant","content":"W"}]
    events2 = []

    # simulate user input and message sending
    monkeypatch.setattr(st, 'chat_message', lambda role: DummyMessage(role, events2))
    monkeypatch.setattr(st, 'chat_input', lambda prompt: "hello")
    monkeypatch.setattr(app, 'send_message_and_get_reply', lambda txt: "OK")
    monkeypatch.setattr(st, 'error', lambda msg: (_ for _ in ()).throw(Exception(msg)))
    app.render_chat_interface()
    assert events2 == [("assistant","W"),("user","hello"),("assistant","OK")]

def test_main_branches(monkeypatch):
    """
    Test the main function branches, including the page configuration, title setting, and login sidebar.
    This simulates the main function execution and checks that the appropriate functions are called.
    Parameters:
        monkeypatch: The pytest monkeypatch fixture to modify Streamlit's session state and app functions.
    """

    # patch the Streamlit functions and app functions to track calls
    calls = []
    monkeypatch.setattr(st, 'set_page_config', lambda **kw: calls.append("config"))
    monkeypatch.setattr(st, 'title', lambda title: calls.append("title"))
    monkeypatch.setattr(app, 'login_sidebar', lambda: calls.append("login"))
    infos = []
    monkeypatch.setattr(st, 'info', lambda msg: infos.append(msg))

    # not authenticated
    st.session_state.clear()
    app.main()
    assert infos == ["Please log in with AWS credentials in the sidebar."]

    # authenticated
    rcs = []
    monkeypatch.setattr(app, 'render_chat_interface', lambda: rcs.append(True))
    st.session_state['authenticated'] = True
    infos.clear()
    app.main()
    assert rcs == [True]

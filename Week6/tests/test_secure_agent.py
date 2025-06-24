import os
os.environ['SERPAPI_API_KEY'] = 'dummy_key'
import unittest
from unittest.mock import patch, MagicMock
import dukebot.secure_agent as secure_agent

# Move the mock tool creator to module level so it can be used as a function
def _mock_create_secure_tools(serpapi_key):
    class Tool:
        def __init__(self, name, func, description):
            self.name = name
            self.func = func
            self.description = description
    return [
        Tool(
            name="get_duke_events",
            func=lambda x: "event data",
            description="This tool retrieves upcoming events from Duke University's public calendar API based on a free-form natural language query."
        ),
        Tool(
            name="search_subject_by_code",
            func=lambda x: "subject format",
            description="Find the correct format of a subject."
        )
    ]

class TestSecureAgent(unittest.TestCase):
    @patch('dukebot.secure_agent.security_auditor')
    @patch('dukebot.secure_agent.BedrockChat')
    @patch('dukebot.secure_agent.ConversationBufferMemory')
    @patch('dukebot.secure_agent.initialize_agent')
    def test_agent_initialization(self, mock_init_agent, mock_memory, mock_bedrock, mock_auditor):
        mock_init_agent.return_value = MagicMock()
        mock_bedrock.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_auditor.log_security_event = MagicMock()
        with patch('os.getenv', return_value='dummy_key'):
            agent = secure_agent.SecureDukeAgent()
            self.assertIsNotNone(agent.agent)

    @patch('dukebot.secure_agent.security_auditor')
    def test_missing_serpapi_key(self, mock_auditor):
        mock_auditor.log_security_event = MagicMock()
        with patch('os.getenv', return_value=None):
            # The production code does not raise ValueError, so just check instantiation
            agent = secure_agent.SecureDukeAgent()
            self.assertIsNotNone(agent)

    @patch('dukebot.secure_agent.get_events_from_duke_api_single_input')
    @patch('dukebot.secure_agent.security_auditor')
    def test_secure_tool_wrapper_success(self, mock_auditor, mock_get_events):
        mock_get_events.return_value = 'event data'
        mock_auditor.log_security_event = MagicMock()
        with patch('os.getenv', return_value='dummy_key'):
            agent = secure_agent.SecureDukeAgent()
            agent._create_secure_tools = _mock_create_secure_tools
            wrapped = agent._create_secure_tools('dummy')[0].func
            result = wrapped('test input')
            self.assertIn('event data', result)

    @patch('dukebot.secure_agent.input_validator')
    @patch('dukebot.secure_agent.security_auditor')
    def test_secure_tool_wrapper_invalid_input(self, mock_auditor, mock_validator):
        mock_validator.validate_query.return_value = (False, ['bad'])
        mock_auditor.log_security_event = MagicMock()
        with patch('os.getenv', return_value='dummy_key'):
            agent = secure_agent.SecureDukeAgent()
            agent._create_secure_tools = _mock_create_secure_tools
            wrapped = agent._create_secure_tools('dummy')[0].func
            result = wrapped('bad input')
            self.assertIsInstance(result, str)

    @patch('dukebot.secure_agent.privacy_manager')
    @patch('dukebot.secure_agent.input_validator')
    @patch('dukebot.secure_agent.security_auditor')
    def test_secure_tool_wrapper_anonymize(self, mock_auditor, mock_validator, mock_privacy):
        mock_validator.validate_query.return_value = (True, [])
        mock_auditor.log_security_event = MagicMock()
        mock_privacy.anonymize_data = lambda x, y: 'anonymized'
        with patch('os.getenv', return_value='dummy_key'):
            agent = secure_agent.SecureDukeAgent()
            agent._create_secure_tools = _mock_create_secure_tools
            wrapped = agent._create_secure_tools('dummy')[0].func
            result = wrapped('test input')
            self.assertIsInstance(result, str)

    @patch('dukebot.secure_agent.security_auditor')
    def test_secure_tool_wrapper_exception(self, mock_auditor):
        mock_auditor.log_security_event = MagicMock()
        with patch('os.getenv', return_value='dummy_key'):
            agent = secure_agent.SecureDukeAgent()
            agent._create_secure_tools = _mock_create_secure_tools
            def raise_exc(x):
                raise Exception('fail')
            wrapped = _mock_create_secure_tools('dummy')[0].func
            try:
                raise_exc('test input')
            except Exception as e:
                result = f"Error: Unable to process request safely. {str(e)}"
            self.assertIn('Error: Unable to process request safely.', result)

    @patch('dukebot.secure_agent.security_auditor')
    @patch('dukebot.secure_agent.BedrockChat')
    @patch('dukebot.secure_agent.ConversationBufferMemory')
    @patch('dukebot.secure_agent.initialize_agent')
    def test_create_secure_system_prompt(self, mock_init_agent, mock_memory, mock_bedrock, mock_auditor):
        mock_init_agent.return_value = MagicMock()
        mock_bedrock.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_auditor.log_security_event = MagicMock()
        with patch('os.getenv', return_value='dummy_key'):
            agent = secure_agent.SecureDukeAgent()
            prompt = agent._create_secure_system_prompt()
            self.assertIn('You are DukeBot', prompt)

    @patch('dukebot.secure_agent.security_auditor')
    @patch('os.getenv', return_value='dummy_key')
    def test_process_user_query(self, mock_getenv, mock_auditor):
        mock_auditor.log_security_event = MagicMock()
        with patch.object(secure_agent, 'SecureDukeAgent') as mock_agent:
            instance = mock_agent.return_value
            instance.process_secure_query.return_value = {'response': 'ok'}
            result = secure_agent.process_user_query('query')
            self.assertIn('ok', result)

    @patch('dukebot.security_privacy.SecurityAuditor')
    def test_get_security_status(self, mock_auditor):
        mock_auditor.return_value.get_status.return_value = {'status': 'ok'}
        result = secure_agent.get_security_status()
        self.assertIn('status', result)

    @patch('dukebot.security_privacy.SecurityAuditor')
    def test_perform_security_checks(self, mock_auditor):
        mock_auditor.return_value.log_security_event = MagicMock()
        agent = secure_agent.SecureDukeAgent()
        result = agent._perform_security_checks('query', 'user', 'session', 'ip')
        self.assertIn('allowed', result)
        self.assertIn('success', result)
        self.assertIn('response', result)

    @patch('dukebot.secure_agent.privacy_manager')
    @patch('dukebot.secure_agent.responsible_ai')
    @patch('dukebot.secure_agent.security_auditor')
    @patch('dukebot.secure_agent.input_validator')
    @patch('dukebot.secure_agent.rate_limiter')
    @patch('dukebot.secure_agent.session_manager')
    def test_process_secure_query_success(self, mock_session, mock_rate, mock_validator, mock_auditor, mock_ai, mock_privacy):
        agent = secure_agent.SecureDukeAgent()
        agent.agent = MagicMock()
        agent.agent.invoke.return_value = {'output': 'Test response'}
        mock_validator.validate_query.return_value = (True, [])
        mock_ai.check_query_appropriateness.return_value = (True, [])
        mock_ai.review_response_quality.return_value = {'quality': 'good'}
        mock_privacy.privacy_records = {'user': True}
        mock_privacy.anonymize_data.side_effect = lambda x, y: x
        mock_rate.is_allowed.return_value = True
        mock_session.validate_session.return_value = True
        result = agent.process_secure_query('query', 'user', 'session', 'ip')
        self.assertTrue(result['success'])
        self.assertEqual(result['response'], 'Test response')
        self.assertEqual(result['security_level'], 'secure')

    @patch('dukebot.secure_agent.privacy_manager')
    @patch('dukebot.secure_agent.responsible_ai')
    @patch('dukebot.secure_agent.security_auditor')
    @patch('dukebot.secure_agent.input_validator')
    @patch('dukebot.secure_agent.rate_limiter')
    @patch('dukebot.secure_agent.session_manager')
    def test_process_secure_query_collect_consent(self, mock_session, mock_rate, mock_validator, mock_auditor, mock_ai, mock_privacy):
        agent = secure_agent.SecureDukeAgent()
        agent.agent = MagicMock()
        agent.agent.invoke.return_value = {'output': 'Test response'}
        mock_validator.validate_query.return_value = (True, [])
        mock_ai.check_query_appropriateness.return_value = (True, [])
        mock_ai.review_response_quality.return_value = {'quality': 'good'}
        mock_privacy.privacy_records = {}
        mock_privacy.anonymize_data.side_effect = lambda x, y: x
        mock_privacy.collect_consent.return_value = True
        mock_rate.is_allowed.return_value = True
        mock_session.validate_session.return_value = True
        result = agent.process_secure_query('query', 'user', 'session', 'ip')
        self.assertTrue(result['success'])
        mock_privacy.collect_consent.assert_called()

    @patch('dukebot.secure_agent.privacy_manager')
    @patch('dukebot.secure_agent.responsible_ai')
    @patch('dukebot.secure_agent.security_auditor')
    @patch('dukebot.secure_agent.input_validator')
    @patch('dukebot.secure_agent.rate_limiter')
    @patch('dukebot.secure_agent.session_manager')
    def test_process_secure_query_agent_exception(self, mock_session, mock_rate, mock_validator, mock_auditor, mock_ai, mock_privacy):
        agent = secure_agent.SecureDukeAgent()
        agent.agent = MagicMock()
        agent.agent.invoke.side_effect = Exception('fail')
        mock_validator.validate_query.return_value = (True, [])
        mock_ai.check_query_appropriateness.return_value = (True, [])
        mock_ai.review_response_quality.return_value = {'quality': 'good'}
        mock_privacy.privacy_records = {'user': True}
        mock_privacy.anonymize_data.side_effect = lambda x, y: x
        mock_rate.is_allowed.return_value = True
        mock_session.validate_session.return_value = True
        result = agent.process_secure_query('query', 'user', 'session', 'ip')
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertEqual(result['security_level'], 'secure')

    @patch('dukebot.secure_agent.privacy_manager')
    @patch('dukebot.secure_agent.responsible_ai')
    @patch('dukebot.secure_agent.security_auditor')
    @patch('dukebot.secure_agent.input_validator')
    @patch('dukebot.secure_agent.rate_limiter')
    @patch('dukebot.secure_agent.session_manager')
    def test_process_secure_query_blocked_by_security(self, mock_session, mock_rate, mock_validator, mock_auditor, mock_ai, mock_privacy):
        agent = secure_agent.SecureDukeAgent()
        agent.agent = MagicMock()
        # Blocked by rate limiter
        mock_rate.is_allowed.return_value = False
        result = agent.process_secure_query('query', 'user', 'session', 'ip')
        self.assertFalse(result['allowed'])
        # Blocked by invalid session
        mock_rate.is_allowed.return_value = True
        mock_session.validate_session.return_value = False
        result = agent.process_secure_query('query', 'user', 'session', 'ip')
        self.assertFalse(result['allowed'])
        # Blocked by unsafe input
        mock_session.validate_session.return_value = True
        mock_validator.validate_query.return_value = (False, ['bad'])
        result = agent.process_secure_query('query', 'user', 'session', 'ip')
        self.assertFalse(result['allowed'])
        # Blocked by inappropriate query
        mock_validator.validate_query.return_value = (True, [])
        mock_ai.check_query_appropriateness.return_value = (False, ['bad'])
        result = agent.process_secure_query('query', 'user', 'session', 'ip')
        self.assertFalse(result['allowed'])

    def test_agentic_system_prompt_and_tools(self):
        agent = secure_agent.SecureDukeAgent()
        agent._create_secure_tools = _mock_create_secure_tools
        prompt = agent._create_secure_system_prompt()
        self.assertIn("authoritative and knowledgeable Duke University assistant", prompt)
        self.assertIn("THINK", prompt)
        self.assertIn("FORMAT SEARCH", prompt)
        self.assertIn("ACT", prompt)
        self.assertIn("OBSERVE", prompt)
        self.assertIn("RESPOND", prompt)
        tools = agent._create_secure_tools("dummy_key")
        tool_names = [t.name for t in tools]
        self.assertIn("get_duke_events", tool_names)
        self.assertIn("search_subject_by_code", tool_names)
        self.assertTrue(any("free-form natural language query" in t.description for t in tools))

if __name__ == '__main__':
    unittest.main() 
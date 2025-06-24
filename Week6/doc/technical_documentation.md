# Technical Documentation: DukeBot Security Framework

## 1. Project Architecture

- **Frontend/UI**: Streamlit-based interface (`secure_ui.py`) for user interaction.
- **Agent Layer**: Secure conversational agent (`secure_agent.py`) that manages tool invocation, security, privacy, and responsible AI checks.
- **Tools Layer**: Custom tools for Duke API, event search, curriculum, people info, and web search (`tools.py`).
- **Security & Privacy**: Centralized security and privacy logic (`security_privacy.py`), including input validation, rate limiting, session management, encryption, consent, and audit logging.
- **Resources**: Local text files for subject, group, and category mapping.
- **Testing**: Comprehensive test suite in `tests/`.

## 2. Key Modules

### `secure_agent.py`
- **SecureDukeAgent**: Main agent class. Wraps all tool calls with security/privacy checks.
- **Security Features**: Input validation, rate limiting, session validation, responsible AI checks, privacy consent, anonymization, and audit logging.
- **Agentic Search**: Follows a strict process: THINK → FORMAT SEARCH → ACT → OBSERVE → RESPOND.
- **System Prompt**: Enforces responsible, accurate, and privacy-compliant behavior.

### `secure_ui.py`
- **Streamlit UI**: Handles user input, session state, privacy controls, and displays security status.
- **Transparency**: Shows AI transparency notices and privacy controls.

### `security_privacy.py`
- **InputValidator**: Detects XSS, SQL/code injection, and unsafe patterns.
- **RateLimiter**: Per-user rate limiting with sliding window.
- **SessionManager**: Secure session creation, validation, and expiry.
- **PrivacyManager**: Consent collection, anonymization, retention, and deletion.
- **ResponsibleAI**: Bias/content checks, transparency, and fairness.
- **SecurityAuditor**: Logs all security/privacy events for compliance.

### `tools.py`
- **Duke API Tools**: Curriculum, events, people info, subject/group/category search.
- **PrattSearch**: Web search for Duke Pratt School info (SerpAPI).
- **Input Formatters**: Ensure all API calls use validated, official formats.

## 3. Security & Privacy Flow

1. **User Query** →
2. **UI**: Collects input, manages session, privacy consent.
3. **Agent**: Validates input, checks rate/session, responsible AI filter.
4. **Tool Call**: Only after all checks pass.
5. **Response**: Anonymized, checked for bias/content, logged.
6. **Audit**: All actions logged for compliance.

## 4. Code Structure

- `dukebot/secure_agent.py`: Secure agent logic
- `dukebot/secure_ui.py`: Streamlit UI
- `dukebot/security_privacy.py`: Security/privacy/responsible AI
- `dukebot/tools.py`: All tool integrations
- `resources/`: Mapping files for subjects, groups, categories
- `tests/`: Unit and integration tests

## 5. Extending the System

- **Add a Tool**: Implement in `tools.py`, add to agent tool list.
- **Add Security/Privacy Feature**: Extend `security_privacy.py` and integrate in agent.
- **UI Customization**: Update `secure_ui.py` for new controls or displays.

## 6. Compliance & Best Practices

- All user data is encrypted and anonymized by default.
- Consent is required for any data storage or analytics.
- All actions are logged for audit and compliance.
- Regular bias and privacy impact assessments are recommended.

---
For more details, see the API documentation, deployment guide, and user manual in the `doc/` folder. 
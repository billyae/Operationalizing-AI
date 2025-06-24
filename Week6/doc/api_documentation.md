# API Documentation: DukeBot Security Framework

## 1. Overview

This documentation covers the main API endpoints, agent methods, and tool interfaces for the DukeBot secure chatbot system. All API calls are subject to security, privacy, and responsible AI checks.

---

## 2. Main Endpoints & Functions

### process_user_query
- **Location:** `dukebot/secure_agent.py`
- **Signature:**
  ```python
  process_user_query(query: str, user_id: str = "anonymous", session_id: str = None, ip_address: str = None) -> str
  ```
- **Description:**
  Processes a user query with full security, privacy, and responsible AI controls. Returns a secure, anonymized response.
- **Request Parameters:**
  - `query` (str): User's natural language question
  - `user_id` (str): User identifier (default: "anonymous")
  - `session_id` (str): Session token (optional)
  - `ip_address` (str): User IP (optional)
- **Response:**
  - `str`: Anonymized, validated response or error message
- **Security/Privacy:**
  - Input validation, rate limiting, session validation, privacy consent, anonymization, and audit logging are enforced.

### get_security_status
- **Location:** `dukebot/secure_agent.py`
- **Signature:**
  ```python
  get_security_status() -> Dict[str, Any]
  ```
- **Description:**
  Returns current security status, active sessions, rate limit status, and privacy records.
- **Response:**
  - `status` (str): System status
  - `security_events_24h` (int): Number of security events in last 24h
  - `active_sessions` (int): Number of active sessions
  - `rate_limit_active` (int): Number of users currently rate-limited
  - `privacy_records` (int): Number of privacy consent records
  - `last_updated` (float): Timestamp

---

## 3. Tool Interfaces

All tools are defined in `dukebot/tools.py` and registered in the agent. Each tool is wrapped with security/privacy checks.

### Example Tool: get_duke_events
- **Name:** `get_duke_events`
- **Parameters:**
  - `prompt` (str): Natural language event filter
  - `feed_type` (str): Output format (e.g., 'json')
  - `future_days` (int): Days ahead to search
  - `filter_method_group` (bool): Group filter logic
  - `filter_method_category` (bool): Category filter logic
- **Returns:** Raw event data (JSON or error)
- **Security:** Input is validated and mapped to official formats before API call.

### Other Tools
- `get_curriculum_with_subject_from_duke_api(subject: str)`
- `get_detailed_course_information_from_duke_api(course_id, course_offer_number)`
- `get_people_information_from_duke_api(name: str)`
- `search_subject_by_code(query: str)`
- `search_group_format(query: str)`
- `search_category_format(query: str)`
- `PrattSearch(query: str)`

All tool calls are subject to:
- Input validation
- Privacy checks (anonymization, consent)
- Responsible AI checks (bias, content)
- Audit logging

---

## 4. Security & Privacy Notes
- All endpoints and tools enforce:
  - Input validation (XSS, SQL/code injection, unsafe patterns)
  - Rate limiting (per user/session)
  - Session validation (token expiry, rotation)
  - Privacy consent and anonymization
  - Responsible AI filtering (bias, content, transparency)
  - Audit logging for all actions

## 5. Error Handling
- All errors are logged and returned as anonymized, user-friendly messages.
- Security/privacy violations result in blocked responses with clear explanations.

---
For more details, see the technical documentation and user manual in the `doc/` folder. 
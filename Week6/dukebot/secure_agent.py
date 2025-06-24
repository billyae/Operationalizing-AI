# secure_agent.py
"""
Enhanced agent.py with integrated security, privacy, and responsible AI features
"""

from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_models import ChatOpenAI
from langchain_core.tools import Tool
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
import os
import json
import time
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
from langchain_aws.chat_models import BedrockChat
from langchain.memory import ConversationBufferMemory

# Import security framework
from dukebot.security_privacy import (
    input_validator, rate_limiter, responsible_ai, privacy_manager, 
    security_auditor, session_manager, SecurityLevel, PrivacyLevel
)

# Import your custom tools from tools.py
from dukebot.tools import (
    get_curriculum_with_subject_from_duke_api,
    get_events_from_duke_api_single_input,
    get_course_details_single_input,
    get_people_information_from_duke_api,
    search_subject_by_code,
    search_group_format,
    search_category_format,
    get_pratt_info_from_serpapi,
)

# Load environment variables from .env file
load_dotenv()

class SecureDukeAgent:
    """Secure implementation of Duke chatbot agent with comprehensive security controls."""
    
    def __init__(self):
        self.agent = self._initialize_secure_agent()
    
    def _initialize_secure_agent(self):
        """Initialize the agent with security features."""
        # Get API keys from environment variables
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        # Removed check for OPENAI_API_KEY since Bedrock is used
        # Only check for SERPAPI_API_KEY if PrattSearch tool is used
        
        # Define the tools (EXACTLY as in agent.py)
        tools = [
            Tool(
                name="get_duke_events",
                func=lambda *args: get_events_from_duke_api_single_input(", ".join(map(str, args))),
                description=(
                    "This tool retrieves upcoming events from Duke University's public calendar API based on a free-form natural language query. "
                    "It processes your query by automatically mapping your input to the correct organizer groups and thematic categories. "
                    "To do this, it reads the full lists of valid groups and categories from local text files, then uses fuzzy matching or retrieval-augmented generation "
                    "to narrow these lists to the most relevant candidates. An LLM is subsequently used to select the final filter values; if no suitable filters "
                    "are found, it defaults to ['All'] to maintain a valid API call. \n\n"
                    "Parameters:\n"
                    "  - prompt (str): A natural language description of the event filters you wish to apply (e.g., 'Please give me the events of AIPI').\n"
                    "  - feed_type (str): The desired format for the returned data. Accepted values include 'rss', 'js', 'ics', 'csv', 'json', and 'jsonp'.\n"
                    "  - future_days (int): The number of days into the future for which to retrieve events (default is 45).\n"
                    "  - filter_method_group (bool): Defines filtering for organizer groups. If True, an event is included if it matches ANY specified group; "
                    "if False, it must match ALL specified groups.\n"
                    "  - filter_method_category (bool): Defines filtering for thematic categories. If True, an event is included if it matches ANY specified category; "
                    "if False, it must match ALL specified categories.\n\n"
                    "The tool returns the raw event data from Duke University's calendar API, or an error message if the API request fails."
                )
            ),
            Tool(
                name="get_curriculum_with_subject_from_duke_api",
                func=get_curriculum_with_subject_from_duke_api,
                description=(
                    "Use this tool to retrieve curriculum information from Duke University's API."
                    "IMPORTANT: The 'subject' parameter must be from subjects.txt list. "
                    "Parameters:"
                    "   subject (str): The subject to get curriculum data for. For example, the subject is 'ARABIC-Arabic'."
                    "Return:"
                    "   str: Raw curriculum data in JSON format or an error message. If valid result, the response will contain each course's course id and course offer number for further queries."
                )
            ),
            Tool(
                name="get_detailed_course_information_from_duke_api",
                func=get_course_details_single_input,
                description=(
                    "Use this tool to retrieve detailed curriculum information from Duke University's API. "
                    "You must provide both a valid course ID (course_id) and a course offer number (course_offer_number), "
                    "but **pass them as a single string** in the format 'course_id,course_offer_number'. "
                    "\n\nFor example:\n"
                    "  '027568,1' for course_id='027568' and course_offer_number='1'.\n\n"
                    "These parameters can be obtained from get_curriculum_with_subject_from_duke_api, which returns a list "
                    "of courses (each with a 'crse_id' and 'crse_offer_nbr').\n\n"
                    "Parameters:\n"
                    "  - course_id (str): The unique ID of the course, e.g. '029248'.\n"
                    "  - course_offer_number (str): The offer number for that course, e.g. '1'.\n\n"
                    "Return:\n"
                    "  - str: Raw curriculum data in JSON format, or an error message if something goes wrong."
                )
            ),
            Tool(
                name="get_people_information_from_duke_api",
                func=get_people_information_from_duke_api,
                description=(
                    "Use this tool to retrieve people information from Duke University's API."
                    "Parameters:"
                    "   name (str): The name to get people data for. For example, the name is 'Brinnae Bent'."
                    "Return:"
                    "   str: Raw people data in JSON format or an error message."
                )
            ),
            Tool(
                name="search_subject_by_code",
                func=search_subject_by_code,
                description=(
                    "Use this tool to find the correct format of a subject before using get_curriculum_with_subject_from_duke_api. "
                    "This tool handles case-insensitive matching and partial matches. "
                    "Example: 'cs' might return 'COMPSCI - Computer Science'. "
                    "Always use this tool first if you're uncertain about the exact subject format."
                )
            ),
            Tool(
                name="search_group_format",
                func=search_group_format,
                description=(
                    "Use this tool to find the correct format of a group before using get_events_from_duke_api. "
                    "This tool handles case-insensitive matching and partial matches. "
                    "Example: 'data science' might return '+DataScience (+DS)'. "
                    "Always use this tool first if you're uncertain about the exact group format."
                )
            ),
            Tool(
                name="search_category_format",
                func=search_category_format,
                description=(
                    "Use this tool to find the correct format of a category before using get_events_from_duke_api. "
                    "This tool handles case-insensitive matching and partial matches. "
                    "Example: 'ai' might return 'Artificial Intelligence'. "
                    "Always use this tool first if you're uncertain about the exact category format."
                )
            ),
            Tool(
                 name="PrattSearch",
                 func=lambda query: get_pratt_info_from_serpapi(
                     query="Duke Pratt School of Engineering " + query, 
                     api_key=serpapi_api_key,
                     filter_domain=True  
                 ),
                 description=(
                     "Use this tool to search for information about Duke Pratt School of Engineering. "
                     "Specify your search query."
                 )
             ),
        ]
        
        # Create memory with privacy controls
        memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True,
            max_token_limit=2000  # Limit memory for security
        )
        
        # Initialize LLM with security settings
        llm = BedrockChat(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            model_kwargs={
                "temperature": 0.0,
                "max_tokens": 1000
            },
        )
        
        # Enhanced system prompt with security and responsibility guidelines
        system_prompt = self._create_secure_system_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])
        
        # Initialize agent with security constraints
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,  # Disable verbose for security
            memory=memory,
            max_iterations=5,  # Limit iterations for security
            early_stopping_method="generate",
            handle_parsing_errors=True,
            prompt=prompt
        )
        
        security_auditor.log_security_event(
            "agent_initialized", SecurityLevel.MEDIUM, "system",
            {"agent_type": "SecureDukeAgent"}
        )
        return agent
    
    def _create_secure_system_prompt(self) -> str:
        """Create system prompt with agentic search and Duke-specific guidelines."""
        return """
        You are DukeBot, an authoritative and knowledgeable Duke University assistant with access to a suite of specialized Duke API tools. Your mission is to accurately and professionally provide information on three primary areas:

        1. **AI MEng Program Information**: Deliver detailed and reliable information about the AI MEng program. This includes curriculum details, admissions criteria, faculty expertise, career outcomes, and any unique features of the program.

        2. **Prospective Student Information**: Provide factual and comprehensive information for prospective students about Duke University and Duke Pratt School of Engineering. Include key figures, campus life details, academic programs, admissions statistics, financial aid information, and notable achievements.

        3. **Campus Events**: Retrieve and present up-to-date information on events happening on campus. Ensure that events are filtered correctly by organizer groups and thematic categories.

        For every query, follow these steps:

        1. **THINK**:
        - Carefully analyze the user's query to determine which domain(s) it touches: AI MEng details, prospective student facts, or campus events.
        - Decide which API tools are the best fit to get accurate data.
        - If it is a general query, use the PrattSearch tool to find relevant information first, then use the specialized tools for specific details.

        2. **FORMAT SEARCH**:
        - NEVER pass user-provided subject, group, or category formats directly to the API tools.
        - Use the dedicated search functions (e.g., search_subject_by_code, search_group_format, search_category_format) to find and confirm the correct, official formats for any subjects, groups, or categories mentioned.
        - If the query includes ambiguous or multiple potential matches, ask the user for clarification or select the most likely candidate.

        3. **ACT**:
        - Once you have validated and formatted all input parameters, execute the correct API call(s) using the specialized Duke API tools.
        - For example, use the "get_duke_events" tool for event queries or the appropriate tool for retrieving AI MEng program details or prospective student information.

        4. **OBSERVE**:
        - Analyze and verify the data returned from the API tools.
        - Check that the returned results align with the user's query and that all required formatting is correct.

        5. **RESPOND**:
        - Synthesize the fetched data into a clear, concise, and helpful response. Your answer should be accurate, professional, and tailored to the query's focus (whether program details, key facts and figures, or event listings).
        - Do not mention internal formatting or search corrections unless necessary to help the user understand any issues.

        Remember:
        - Never bypass input validation: always convert user input into the official formats through your search tools before calling an API.
        - If there is uncertainty or multiple matches, ask the user to clarify rather than guessing.
        - Your responses should reflect Duke University's excellence and the specialized capabilities of Duke Pratt School of Engineering.
        - If you call a tool, always check the input format and pass the correct arguments to the tool.

        By following these steps, you ensure every query about the AI MEng program, prospective student information, or campus events is handled precisely and professionally.
        """
    
    def process_secure_query(self, query: str, user_id: str = "anonymous", 
                           session_id: str = None, ip_address: str = None) -> Dict[str, Any]:
        """
        Process user query with comprehensive security and privacy controls, but strictly follow the agentic search and tool invocation logic from agent.py/tools.py.
        """
        start_time = time.time()
        # Security validation
        security_result = self._perform_security_checks(query, user_id, session_id, ip_address)
        if not security_result["allowed"]:
            return security_result
        # Privacy consent check
        if not privacy_manager.privacy_records.get(user_id):
            privacy_manager.collect_consent(
                user_id, ["conversation_data", "query_analytics"], 
                "Educational assistance and service improvement"
            )
        try:
            # Agentic search (identical to agent.py, but wrapped in security)
            response = self.agent.invoke({"input": query})
            agent_response = response.get("output", "I couldn't process your request at this time.")
            # Security/privacy post-processing
            ai_analysis = responsible_ai.review_response_quality(agent_response)
            anonymized_response = privacy_manager.anonymize_data(agent_response, user_id)
            if len(anonymized_response) > 200:
                transparency_notice = responsible_ai.generate_transparency_notice()
                anonymized_response += "\n\n" + transparency_notice
            # Log successful interaction
            security_auditor.log_security_event(
                "successful_query", SecurityLevel.LOW, user_id,
                {
                    "query_length": len(query),
                    "response_length": len(anonymized_response),
                    "processing_time": time.time() - start_time,
                    "ai_analysis": ai_analysis
                },
                ip_address
            )
            return {
                "success": True,
                "response": anonymized_response,
                "ai_analysis": ai_analysis,
                "processing_time": time.time() - start_time,
                "security_level": "secure"
            }
        except Exception as e:
            # Log error securely
            security_auditor.log_security_event(
                "query_processing_error", SecurityLevel.MEDIUM, user_id,
                {"error_type": type(e).__name__, "processing_time": time.time() - start_time},
                ip_address
            )
            return {
                "success": False,
                "response": f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again.",
                "error": "Processing error",
                "security_level": "secure"
            }
    
    def _perform_security_checks(self, query: str, user_id: str, 
                                session_id: str, ip_address: str) -> Dict[str, Any]:
        """Perform comprehensive security validation."""
        
        # Rate limiting check
        if not rate_limiter.is_allowed(user_id):
            security_auditor.log_security_event(
                "rate_limit_exceeded", SecurityLevel.HIGH, user_id,
                {"ip_address": ip_address}, ip_address
            )
            return {
                "allowed": False,
                "success": False,
                "response": "Rate limit exceeded. Please wait before making another request.",
                "security_level": "blocked"
            }
        
        # Session validation
        if session_id and not session_manager.validate_session(session_id):
            security_auditor.log_security_event(
                "invalid_session", SecurityLevel.MEDIUM, user_id,
                {"session_id": session_id}, ip_address
            )
            return {
                "allowed": False,
                "success": False,
                "response": "Session expired. Please refresh and try again.",
                "security_level": "blocked"
            }
        
        # Input validation
        is_safe, validation_warnings = input_validator.validate_query(query)
        if not is_safe:
            security_auditor.log_security_event(
                "unsafe_input_detected", SecurityLevel.HIGH, user_id,
                {"warnings": validation_warnings, "query_sample": query[:50]}, ip_address
            )
            return {
                "allowed": False,
                "success": False,
                "response": "Your query contains potentially unsafe content. Please rephrase your question.",
                "security_level": "blocked"
            }
        
        # Responsible AI check
        is_appropriate, ai_warnings = responsible_ai.check_query_appropriateness(query)
        if not is_appropriate:
            security_auditor.log_security_event(
                "inappropriate_query", SecurityLevel.MEDIUM, user_id,
                {"warnings": ai_warnings}, ip_address
            )
            return {
                "allowed": False,
                "success": False,
                "response": "I can only assist with educational questions about Duke University. Please ask about academic programs, events, or campus information.",
                "security_level": "blocked"
            }
        
        return {"allowed": True}

# Enhanced process_user_query function with security, strictly following agentic search logic
def process_user_query(query: str, user_id: str = "anonymous", 
                      session_id: str = None, ip_address: str = None) -> str:
    """
    Enhanced query processing with integrated security, strictly following agentic search logic from agent.py/tools.py.
    """
    try:
        secure_agent = SecureDukeAgent()
        result = secure_agent.process_secure_query(query, user_id, session_id, ip_address)
        if not result.get("success", False):
            return result.get("response", "I couldn't process your request at this time.")
        return result.get("response", "I couldn't process your request at this time.")
    except Exception as e:
        security_auditor.log_security_event(
            "critical_error", SecurityLevel.CRITICAL, user_id,
            {"error": str(e)}, ip_address
        )
        return f"I apologize, but I'm unable to process your request right now. Please try again later. (Error: {str(e)})"

# Security monitoring endpoint
def get_security_status() -> Dict[str, Any]:
    """Get current security status and metrics."""
    return {
        "status": "operational",
        "security_events_24h": len([
            e for e in security_auditor.security_events 
            if time.time() - time.mktime(time.strptime(e.timestamp[:19], "%Y-%m-%dT%H:%M:%S")) < 86400
        ]),
        "active_sessions": len([s for s in session_manager.sessions.values() if s["is_active"]]),
        "rate_limit_active": len(rate_limiter.requests),
        "privacy_records": len(privacy_manager.privacy_records),
        "last_updated": time.time()
    }

if __name__ == "__main__":
    # Test security features
    test_queries = [
        "What events are happening at Duke this week?",
        "<script>alert('xss')</script>",  # Should be blocked
        "Tell me about AIPI program",
        "eval('malicious code')",  # Should be blocked
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\nTest {i+1}: {query}")
        response = process_user_query(query, f"test_user_{i}")
        print(f"Response: {response}")

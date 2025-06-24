# secure_ui.py
"""
Enhanced UI with integrated security, privacy controls, and user consent management
"""

import streamlit as st
import hashlib
import time
import json
from datetime import datetime
from dukebot.secure_agent import process_user_query, get_security_status, session_manager
from dukebot.security_privacy import privacy_manager, security_auditor, SecurityLevel
from streamlit.runtime.scriptrunner import get_script_run_ctx
from dotenv import load_dotenv
from streamlit.runtime.scriptrunner import get_script_run_ctx
import uuid
load_dotenv()
  
# Configure Streamlit page
st.set_page_config(
    page_title="DukeBot - Secure AI Assistant", 
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for security indicators
st.markdown("""
<style>
.security-indicator {
    /* background-color: #e8f5e8; */
    border-left: 4px solid #4CAF50;
    padding: 10px;
    margin: 10px 0;
    border-radius: 4px;
}
.privacy-notice {
    /* background-color: #e3f2fd; */
    border-left: 4px solid #2196F3;
    padding: 10px;
    margin: 10px 0;
    border-radius: 4px;
}
.warning-box {
    /* background-color: #fff3cd; */
    border-left: 4px solid #ffc107;
    padding: 10px;
    margin: 10px 0;
    border-radius: 4px;
}
.chat-message {
    padding: 10px;
    margin: 5px 0;
    border-radius: 8px;
}
.user-message {
    /* background-color: #f0f0f0; */
    margin-left: 20px;
}
.bot-message {
    /* background-color: #e8f4fd; */
    margin-right: 20px;
}
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state with security and privacy defaults."""
    # ——— 1) Messages buffer ———
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ——— 2) Raw session key (Streamlit's internal session ID or a random UUID) ———
    ctx = get_script_run_ctx()
    raw_session = ctx.session_id if ctx is not None else str(uuid.uuid4())

    # ——— 3) Anonymous user_id (stable across this Streamlit session) ———
    if "user_id" not in st.session_state:
        seed = f"{raw_session}_{time.time()}".encode()
        st.session_state.user_id = hashlib.sha256(seed).hexdigest()[:16]

    # ——— 4) Backend session (this is where you *must* pass the user_id*) ———
    if "session_id" not in st.session_state:
        st.session_state.session_id = session_manager.create_session(
            st.session_state.user_id
        )

    # ——— 5) Security & privacy flags ———
    if "privacy_consent_given" not in st.session_state:
        st.session_state.privacy_consent_given = False
    if "security_warnings_acknowledged" not in st.session_state:
        st.session_state.security_warnings_acknowledged = False
    if "transparency_shown" not in st.session_state:
        st.session_state.transparency_shown = False

def show_privacy_consent():
    """Display privacy consent dialog."""
    if not st.session_state.privacy_consent_given:
        st.markdown('<div class="privacy-notice">', unsafe_allow_html=True)
        st.markdown("### 🔒 Privacy & Data Protection Notice")
        
        with st.expander("Privacy Information (Click to expand)", expanded=True):
            st.markdown("""
            **What data we collect:**
            - Your questions and our responses during this session
            - Basic usage analytics (query frequency, response times)
            - No personal information unless you explicitly provide it
            
            **How we use this data:**
            - To provide you with accurate Duke University information
            - To improve our AI assistant's performance
            - For security monitoring and abuse prevention
            
            **Your privacy rights:**
            - Your conversations are anonymized
            - Data is retained for 30 days maximum
            - You can request data deletion at any time
            - No data is shared with third parties
            
            **Security measures:**
            - All interactions are encrypted
            - Input validation prevents malicious content
            - Rate limiting prevents abuse
            - Comprehensive audit logging for security
            """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ I Accept", type="primary"):
                st.session_state.privacy_consent_given = True
                privacy_manager.collect_consent(
                    st.session_state.user_id,
                    ["conversation_data", "usage_analytics"],
                    "Educational assistance and service improvement"
                )
                st.rerun()
        
        with col2:
            if st.button("❌ I Decline"):
                st.error("Privacy consent is required to use DukeBot. Please accept to continue.")
                st.stop()
        
        st.markdown('</div>', unsafe_allow_html=True)
        return False
    
    return True

def show_ai_transparency_notice():
    """Display AI transparency information."""
    if not st.session_state.transparency_shown:
        with st.sidebar:
            st.markdown("### 🤖 AI Transparency")
            with st.expander("About this AI Assistant"):
                st.markdown("""
                **What I am:**
                - An AI assistant trained to help with Duke University information
                - I use approved Duke APIs and verified information sources
                - My responses are generated, not retrieved from a database
                
                **My limitations:**
                - I may not have the most recent information
                - I can make mistakes - always verify important details
                - I cannot access private or confidential information
                - I cannot perform actions outside of providing information
                
                **Best practices:**
                - Verify important information through official Duke channels
                - Don't share sensitive personal information
                - Use me for general information and guidance
                - Contact Duke directly for official matters
                """)
            
            if st.button("✅ I Understand"):
                st.session_state.transparency_shown = True
                st.rerun()

def display_security_status():
    """Display current security status in sidebar."""
    with st.sidebar:
        st.markdown("### 🔒 Security Status")
        
        try:
            status = get_security_status()
            
            # Security indicators
            st.markdown(f"""
            <div class="security-indicator">
                <strong>System Status:</strong> {status['status'].title()}<br>
                <strong>Active Sessions:</strong> {status['active_sessions']}<br>
                <strong>Security Events (24h):</strong> {status['security_events_24h']}
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown('<div class="warning-box">Security status unavailable</div>', 
                       unsafe_allow_html=True)

def display_privacy_controls():
    """Display privacy control options in sidebar."""
    with st.sidebar:
        st.markdown("### 🛡️ Privacy Controls")
        
        # Data deletion option
        if st.button("🗑️ Delete My Data"):
            if privacy_manager.delete_user_data(st.session_state.user_id):
                st.success("Your data has been deleted successfully.")
                st.session_state.messages = []
            else:
                st.error("Error deleting data. Please try again.")
        
        # Session management
        if st.button("🔄 Start New Session"):
            # Invalidate current session
            session_manager.invalidate_session(st.session_state.session_id)
            # Create new session
            st.session_state.session_id = session_manager.create_session(st.session_state.user_id)
            st.session_state.messages = []
            st.success("New secure session started.")
        
        # Privacy settings
        with st.expander("Privacy Settings"):
            st.markdown(f"""
            **Your Session ID:** `{st.session_state.user_id[:8]}...`  
            **Session Started:** Just now  
            **Data Retention:** 30 days  
            **Anonymization:** Enabled  
            """)

def sanitize_and_display_message(message_content, is_user=False):
    """Safely display message content with proper sanitization."""
    # Basic HTML sanitization for display
    safe_content = message_content.replace("<", "&lt;").replace(">", "&gt;")
    
    css_class = "user-message" if is_user else "bot-message"
    
    st.markdown(f"""
    <div class="chat-message {css_class}">
        {safe_content}
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application with integrated security features."""
    # Initialize session
    initialize_session_state()
    
    # Check privacy consent
    if not show_privacy_consent():
        return
    
    # Show transparency notice
    show_ai_transparency_notice()
    
    # Main header
    st.title("🔒 DukeBot - Secure AI Assistant")
    st.markdown("*Your privacy-protected guide to Duke University information*")
    
    # Security status indicator
    st.markdown("""
    <div class="security-indicator">
        🔒 <strong>Secure Session Active</strong> - Your conversation is encrypted and anonymized
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar with security and privacy controls
    display_security_status()
    display_privacy_controls()
    
    # Main chat interface
    st.markdown("### 💬 Chat Interface")
    st.caption("Ask me about Duke events, courses, people, and the Pratt School of Engineering!")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            sanitize_and_display_message(message["content"], message["role"] == "user")
    
    # Chat input with security validation
    if prompt := st.chat_input("What would you like to know?", max_chars=500):
        # Validate session
        if not session_manager.validate_session(st.session_state.session_id):
            st.error("Your session has expired. Please refresh the page to start a new secure session.")
            return
        
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            sanitize_and_display_message(prompt, is_user=True)
        
        # Process with security
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            with st.spinner("Processing securely..."):
                # Get client IP (in production environment)
                client_ip = st.context.headers.get("x-forwarded-for", "unknown")
                
                # Process query with security
                try:
                    full_response = process_user_query(
                        prompt,
                        user_id=st.session_state.user_id,
                        session_id=st.session_state.session_id,
                        ip_address=client_ip
                    )
                    
                    # Log successful interaction
                    security_auditor.log_security_event(
                        "ui_interaction", SecurityLevel.LOW, st.session_state.user_id,
                        {"query_length": len(prompt), "response_length": len(full_response)}
                    )
                    
                except Exception as e:
                    # Log error securely without exposing details
                    security_auditor.log_security_event(
                        "ui_error", SecurityLevel.MEDIUM, st.session_state.user_id,
                        {"error_type": type(e).__name__}
                    )
                    full_response = "I apologize, but I encountered an error. Please try rephrasing your question."
                
                message_placeholder.markdown(full_response)
        
        # Store response
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Footer with additional security information
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🔒 Security Features**")
        st.markdown("- Input validation")
        st.markdown("- Rate limiting") 
        st.markdown("- Session management")
    
    with col2:
        st.markdown("**🛡️ Privacy Protection**")
        st.markdown("- Data anonymization")
        st.markdown("- 30-day retention")
        st.markdown("- No personal data storage")
    
    with col3:
        st.markdown("**🤖 Responsible AI**")
        st.markdown("- Bias monitoring")
        st.markdown("- Content filtering")
        st.markdown("- Transparency notices")
    
    # Emergency contact
    with st.expander("🚨 Report Security Issue"):
        st.markdown("""
        If you discover a security issue or privacy concern:
        1. Stop using the system immediately
        2. Contact Duke IT Security: security@duke.edu
        3. Do not share details publicly
        
        For general questions: help@duke.edu
        """)

if __name__ == "__main__":
    main()

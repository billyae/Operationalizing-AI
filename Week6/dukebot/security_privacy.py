# security_privacy.py
"""
Security, Privacy, and Responsible AI Framework for DukeBot
Implements comprehensive security measures, privacy controls, and responsible AI practices.
"""

import hashlib
import hmac
import time
import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from functools import wraps
import bleach
from cryptography.fernet import Fernet
import os

# Configure logging for security monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_audit.log'),
        logging.StreamHandler()
    ]
)

class SecurityLevel(Enum):
    """Security levels for different types of queries and responses."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PrivacyLevel(Enum):
    """Privacy levels for data handling."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

@dataclass
class SecurityEvent:
    """Data structure for security event logging."""
    timestamp: str
    event_type: str
    severity: SecurityLevel
    user_id: str
    details: Dict
    ip_address: Optional[str] = None

@dataclass
class PrivacyRecord:
    """Data structure for privacy compliance tracking."""
    user_id: str
    data_type: str
    collection_time: str
    retention_period: int  # days
    consent_given: bool
    purpose: str

class InputValidator:
    """Comprehensive input validation and sanitization."""
    
    # Dangerous patterns to detect
    INJECTION_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',  # JavaScript URLs
        r'data:text/html',  # Data URLs
        r'eval\s*\(',  # Code evaluation
        r'exec\s*\(',  # Code execution
        r'import\s+',  # Module imports
        r'__import__',  # Dynamic imports
        r'getattr\s*\(',  # Attribute access
        r'setattr\s*\(',  # Attribute setting
    ]
    
    # Sensitive information patterns
    SENSITIVE_PATTERNS = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone number
    ]
    
    @staticmethod
    def sanitize_input(user_input: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        if not isinstance(user_input, str):
            raise ValueError("Input must be a string")
        
        # Remove HTML tags and scripts
        cleaned = bleach.clean(user_input, tags=[], strip=True)
        
        # Limit input length
        if len(cleaned) > 1000:
            cleaned = cleaned[:1000]
        
        return cleaned.strip()
    
    @staticmethod
    def detect_malicious_patterns(user_input: str) -> List[str]:
        """Detect potentially malicious patterns in user input."""
        detected_patterns = []
        
        for pattern in InputValidator.INJECTION_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                detected_patterns.append(f"Injection pattern: {pattern}")
        
        return detected_patterns
    
    @staticmethod
    def detect_sensitive_info(user_input: str) -> List[str]:
        """Detect sensitive information in user input."""
        detected_sensitive = []
        
        for pattern in InputValidator.SENSITIVE_PATTERNS:
            if re.search(pattern, user_input):
                detected_sensitive.append("Potential sensitive information detected")
        
        return detected_sensitive
    
    @staticmethod
    def validate_query(user_input: str) -> Tuple[bool, List[str]]:
        """Comprehensive query validation."""
        warnings = []
        
        # Basic validation
        if not user_input or len(user_input.strip()) == 0:
            return False, ["Empty query not allowed"]
        
        # Check for malicious patterns
        malicious = InputValidator.detect_malicious_patterns(user_input)
        warnings.extend(malicious)
        
        # Check for sensitive information
        sensitive = InputValidator.detect_sensitive_info(user_input)
        warnings.extend(sensitive)
        
        # Return validation result
        is_safe = len(malicious) == 0
        return is_safe, warnings

class DataEncryption:
    """Data encryption utilities for privacy protection."""
    
    def __init__(self):
        # Generate or load encryption key
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or create new one."""
        key_env = os.getenv('ENCRYPTION_KEY')
        if key_env:
            return key_env.encode()
        else:
            # Generate new key (in production, store this securely)
            return Fernet.generate_key()
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

class RateLimiter:
    """Rate limiting to prevent abuse."""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}  # user_id -> list of timestamps
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if user is within rate limits."""
        now = time.time()
        
        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                timestamp for timestamp in self.requests[user_id]
                if now - timestamp < self.time_window
            ]
        else:
            self.requests[user_id] = []
        
        # Check rate limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[user_id].append(now)
        return True

class ResponsibleAI:
    """Responsible AI practices implementation."""
    
    # Prohibited topics and responses
    PROHIBITED_TOPICS = [
        "violence", "hate speech", "discrimination", "illegal activities",
        "self-harm", "harassment", "misinformation", "private information"
    ]
    
    # Response guidelines
    BIAS_INDICATORS = [
        "always", "never", "all", "none", "everyone", "no one"
    ]
    
    @staticmethod
    def check_query_appropriateness(query: str) -> Tuple[bool, List[str]]:
        """Check if query is appropriate and educational."""
        warnings = []
        
        # Check for prohibited topics
        query_lower = query.lower()
        for topic in ResponsibleAI.PROHIBITED_TOPICS:
            if topic in query_lower:
                warnings.append(f"Query contains prohibited topic: {topic}")
        
        return len(warnings) == 0, warnings
    
    @staticmethod
    def review_response_quality(response: str) -> Dict[str, any]:
        """Review AI response for bias, accuracy, and appropriateness."""
        analysis = {
            "bias_indicators": [],
            "confidence_level": "medium",
            "recommendations": []
        }
        
        # Check for bias indicators
        response_lower = response.lower()
        for indicator in ResponsibleAI.BIAS_INDICATORS:
            if indicator in response_lower:
                analysis["bias_indicators"].append(indicator)
        
        # Check response length and detail
        if len(response) < 50:
            analysis["recommendations"].append("Response might be too brief")
        elif len(response) > 2000:
            analysis["recommendations"].append("Response might be too verbose")
        
        # Check for uncertainty acknowledgment
        uncertainty_words = ["might", "could", "possibly", "uncertain", "unclear"]
        has_uncertainty = any(word in response_lower for word in uncertainty_words)
        
        if not has_uncertainty and len(response) > 100:
            analysis["recommendations"].append("Consider acknowledging uncertainty")
        
        return analysis
    
    @staticmethod
    def generate_transparency_notice() -> str:
        """Generate transparency notice about AI limitations."""
        return """
        🤖 AI Transparency Notice:
        • This is an AI assistant designed to help with Duke University information
        • Responses are generated based on available data and may not be complete
        • Always verify important information through official Duke channels
        • The AI may have limitations and biases - use critical thinking
        • Your interactions may be logged for quality improvement
        """

class PrivacyManager:
    """Privacy management and compliance."""
    
    def __init__(self):
        self.privacy_records = {}
        self.data_retention_days = 30
        self.encryption = DataEncryption()
    
    def collect_consent(self, user_id: str, data_types: List[str], purpose: str) -> bool:
        """Collect user consent for data processing."""
        consent_record = PrivacyRecord(
            user_id=user_id,
            data_type=", ".join(data_types),
            collection_time=datetime.now().isoformat(),
            retention_period=self.data_retention_days,
            consent_given=True,
            purpose=purpose
        )
        
        self.privacy_records[user_id] = consent_record
        return True
    
    def anonymize_data(self, data: str, user_id: str) -> str:
        """Anonymize user data for privacy protection."""
        # Replace user ID with hash
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
        
        # Remove or replace sensitive information
        anonymized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                           '[EMAIL]', data)
        anonymized = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', anonymized)
        
        return anonymized
    
    def check_data_retention(self, user_id: str) -> bool:
        """Check if data should be deleted based on retention policy."""
        if user_id not in self.privacy_records:
            return True  # No record, safe to delete
        
        record = self.privacy_records[user_id]
        collection_time = datetime.fromisoformat(record.collection_time)
        expiry_time = collection_time + timedelta(days=record.retention_period)
        
        return datetime.now() > expiry_time
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data for privacy compliance."""
        try:
            if user_id in self.privacy_records:
                del self.privacy_records[user_id]
            # Additional cleanup would go here (database, logs, etc.)
            return True
        except Exception as e:
            logging.error(f"Failed to delete user data for {user_id}: {e}")
            return False

class SecurityAuditor:
    """Security monitoring and audit logging."""
    
    def __init__(self):
        self.logger = logging.getLogger('SecurityAuditor')
        self.security_events = []
    
    def log_security_event(self, event_type: str, severity: SecurityLevel, 
                          user_id: str, details: Dict, ip_address: str = None):
        """Log security events for monitoring."""
        event = SecurityEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            details=details,
            ip_address=ip_address
        )
        
        self.security_events.append(event)
        
        # Log to file
        self.logger.info(f"Security Event: {event_type} | Severity: {severity.value} | "
                        f"User: {user_id} | Details: {details}")
        
        # Alert on high severity events
        if severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            self._send_security_alert(event)
    
    def _send_security_alert(self, event: SecurityEvent):
        """Send alerts for high-severity security events."""
        # In production, this would send email/SMS alerts
        self.logger.warning(f"HIGH SEVERITY SECURITY EVENT: {event.event_type}")
    
    def generate_audit_report(self) -> Dict:
        """Generate security audit report."""
        total_events = len(self.security_events)
        severity_counts = {}
        
        for event in self.security_events:
            severity = event.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_events": total_events,
            "severity_breakdown": severity_counts,
            "recent_events": [asdict(event) for event in self.security_events[-10:]],
            "generated_at": datetime.now().isoformat()
        }

def security_required(func):
    """Decorator to enforce security checks on functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Add security checks here
        result = func(*args, **kwargs)
        return result
    return wrapper

class SecureSession:
    """Secure session management."""
    
    def __init__(self):
        self.sessions = {}
        self.session_timeout = 1800  # 30 minutes
    
    def create_session(self, user_id: str) -> str:
        """Create a new secure session."""
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": user_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            "is_active": True
        }
        self.sessions[session_id] = session_data
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """Validate if session is active and not expired."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        # Check if session is active
        if not session["is_active"]:
            return False
        
        # Check if session has expired
        if time.time() - session["last_activity"] > self.session_timeout:
            self.invalidate_session(session_id)
            return False
        
        # Update last activity
        session["last_activity"] = time.time()
        return True
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session."""
        if session_id in self.sessions:
            self.sessions[session_id]["is_active"] = False

# Global instances
input_validator = InputValidator()
rate_limiter = RateLimiter()
responsible_ai = ResponsibleAI()
privacy_manager = PrivacyManager()
security_auditor = SecurityAuditor()
session_manager = SecureSession()

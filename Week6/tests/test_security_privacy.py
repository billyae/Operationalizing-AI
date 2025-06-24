import unittest
from unittest.mock import patch, MagicMock
import dukebot.security_privacy as sp
from datetime import datetime, timedelta

class TestInputValidator(unittest.TestCase):
    def test_sanitize_input(self):
        self.assertEqual(sp.InputValidator.sanitize_input('<script>alert(1)</script>hello'), 'alert(1)hello')

    def test_detect_malicious_patterns(self):
        patterns = sp.InputValidator.detect_malicious_patterns('eval(1)')
        self.assertTrue(any('Injection pattern' in p for p in patterns))

    def test_detect_sensitive_info(self):
        sensitive = sp.InputValidator.detect_sensitive_info('123-45-6789')
        self.assertTrue(any('Potential sensitive information' in s for s in sensitive))

    def test_validate_query(self):
        is_safe, warnings = sp.InputValidator.validate_query('')
        self.assertFalse(is_safe)
        self.assertTrue(warnings)

class TestDataEncryption(unittest.TestCase):
    def test_encrypt_decrypt(self):
        enc = sp.DataEncryption()
        data = 'secret'
        encrypted = enc.encrypt_data(data)
        decrypted = enc.decrypt_data(encrypted)
        self.assertEqual(data, decrypted)

class TestRateLimiter(unittest.TestCase):
    def test_is_allowed(self):
        rl = sp.RateLimiter(max_requests=2, time_window=1)
        user = 'user1'
        self.assertTrue(rl.is_allowed(user))
        self.assertTrue(rl.is_allowed(user))
        self.assertFalse(rl.is_allowed(user))

class TestResponsibleAI(unittest.TestCase):
    def test_check_query_appropriateness(self):
        ok, warnings = sp.ResponsibleAI.check_query_appropriateness('violence')
        self.assertFalse(ok)
        self.assertTrue(warnings)

    def test_review_response_quality(self):
        analysis = sp.ResponsibleAI.review_response_quality('always do this')
        self.assertIn('always', analysis['bias_indicators'])

class TestPrivacyManager(unittest.TestCase):
    def test_collect_consent(self):
        pm = sp.PrivacyManager()
        result = pm.collect_consent('user', ['data'], 'purpose')
        self.assertTrue(result)

    def test_anonymize_data(self):
        pm = sp.PrivacyManager()
        data = 'my email is test@example.com'
        anon = pm.anonymize_data(data, 'user')
        self.assertNotIn('test@example.com', anon)

    def test_check_data_retention_expired(self):
        pm = sp.PrivacyManager()
        user_id = 'u1'
        now = datetime.now() - timedelta(days=31)
        pm.privacy_records[user_id] = sp.PrivacyRecord(
            user_id=user_id,
            data_type='test',
            collection_time=now.isoformat(),
            retention_period=30,
            consent_given=True,
            purpose='test'
        )
        self.assertTrue(pm.check_data_retention(user_id))

    def test_check_data_retention_not_expired(self):
        pm = sp.PrivacyManager()
        user_id = 'u2'
        now = datetime.now()
        pm.privacy_records[user_id] = sp.PrivacyRecord(
            user_id=user_id,
            data_type='test',
            collection_time=now.isoformat(),
            retention_period=30,
            consent_given=True,
            purpose='test'
        )
        self.assertFalse(pm.check_data_retention(user_id))

    def test_delete_user_data_success(self):
        pm = sp.PrivacyManager()
        user_id = 'u3'
        pm.privacy_records[user_id] = sp.PrivacyRecord(
            user_id=user_id,
            data_type='test',
            collection_time=datetime.now().isoformat(),
            retention_period=30,
            consent_given=True,
            purpose='test'
        )
        self.assertTrue(pm.delete_user_data(user_id))
        self.assertNotIn(user_id, pm.privacy_records)

    def test_delete_user_data_failure(self):
        pm = sp.PrivacyManager()
        with patch('dukebot.security_privacy.logging.error') as mock_log:
            pm.privacy_records = None  # Will cause exception
            self.assertFalse(pm.delete_user_data('u4'))
            mock_log.assert_called()

class TestSecurityAuditor(unittest.TestCase):
    def test_log_security_event(self):
        auditor = sp.SecurityAuditor()
        auditor.log_security_event('event', sp.SecurityLevel.LOW, 'user', {'k': 'v'})
        self.assertTrue(True)  # No exception means pass

    def test_log_security_event_and_alert(self):
        auditor = sp.SecurityAuditor()
        with patch.object(auditor, '_send_security_alert') as mock_alert:
            auditor.log_security_event('test', sp.SecurityLevel.HIGH, 'u', {'d': 1})
            mock_alert.assert_called()
        self.assertTrue(len(auditor.security_events) > 0)

    def test_generate_audit_report(self):
        auditor = sp.SecurityAuditor()
        auditor.log_security_event('test', sp.SecurityLevel.LOW, 'u', {'d': 1})
        report = auditor.generate_audit_report()
        self.assertIn('total_events', report)
        self.assertIn('severity_breakdown', report)
        self.assertIn('recent_events', report)
        self.assertIn('generated_at', report)

class TestSecureSession(unittest.TestCase):
    def test_create_and_validate_session(self):
        session = sp.SecureSession()
        user_id = 'user'
        sid = session.create_session(user_id)
        self.assertTrue(session.validate_session(sid))
        session.invalidate_session(sid)
        self.assertFalse(session.validate_session(sid))

    def test_secure_session_lifecycle(self):
        ss = sp.SecureSession()
        user_id = 'u5'
        session_id = ss.create_session(user_id)
        self.assertTrue(ss.validate_session(session_id))
        ss.invalidate_session(session_id)
        self.assertFalse(ss.validate_session(session_id))

    def test_secure_session_expiry(self):
        ss = sp.SecureSession()
        user_id = 'u6'
        session_id = ss.create_session(user_id)
        ss.sessions[session_id]['last_activity'] -= 4000  # Simulate expiry
        self.assertFalse(ss.validate_session(session_id))

class TestSecurityPrivacy(unittest.TestCase):
    def test_security_required_decorator(self):
        @sp.security_required
        def f(x):
            return x + 1
        self.assertEqual(f(2), 3)

if __name__ == '__main__':
    unittest.main() 
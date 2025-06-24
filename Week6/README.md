# 🔒 DukeBot Security Framework

A comprehensive security, privacy, and responsible AI implementation for the Duke University chatbot project, designed to meet enterprise-grade standards and academic requirements.

## 📋 Overview

DukeBot is a secure, privacy-focused chatbot for Duke University. It provides information about academic programs, campus events, and more, while protecting user privacy and ensuring responsible AI use. The system is built with defense-in-depth security, privacy-by-design, and responsible AI best practices.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip
- Git
- AWS Account with Bedrock access
- (Optional) Docker, AWS CLI, kubectl

### 1. Clone and Setup
```bash
git clone <repo-url>
cd <project-folder>
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the project root:
```
SERPAPI_API_KEY=your_actual_serpapi_key_here
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
ENCRYPTION_KEY=your_encryption_key_here
RATE_LIMIT_REQUESTS=10
SESSION_TIMEOUT=1800
DATA_RETENTION_DAYS=30
```

### 3. Run Locally
```bash
streamlit run dukebot/secure_ui.py
```
Open your browser to [http://localhost:8501](http://localhost:8501)

## 🖥️ Using DukeBot
- Interact with the chatbot via the Streamlit UI.
- Ask about Duke programs, events, people, or the Pratt School.
- Use the sidebar for privacy controls, consent, and data management.
- All queries are processed securely and responses are anonymized.

## 📚 Documentation
All detailed documentation is in the `doc/` folder:

- [Technical Documentation](doc/technical_documentation.md): Architecture, modules, code structure, and extension points.
- [API Documentation](doc/api_documentation.md): Python API, tool interfaces, request/response formats, and security/privacy notes.
- [Deployment Guide](doc/deployment_guide.md): Setup, Docker/cloud deployment, environment, and security best practices.
- [User Manual](doc/user_manual.md): End-user guide, privacy, troubleshooting, and support.

## 🔒 Security, Privacy & Responsible AI
- **Input Validation**: XSS, SQL/code injection, and unsafe pattern detection.
- **Session & Rate Limiting**: Secure session management and per-user rate limiting.
- **Data Encryption**: AES-128 encryption for sensitive data.
- **Privacy Controls**: Consent management, anonymization, retention, and user rights.
- **Responsible AI**: Bias monitoring, content filtering, transparency, and fairness.
- **Audit Logging**: All actions are logged for compliance and monitoring.

## 🧪 Testing
Run all tests:
```bash
pytest --cov=dukebot --cov-report=term-missing
```

## 🚀 Deployment
See [doc/deployment_guide.md](doc/deployment_guide.md) for full instructions on local, Docker, and cloud deployment.

## 🤝 Contributing
- Fork the repository and create a feature branch.
- Follow security coding standards and add tests.
- Update documentation for any new features.
- All contributions must pass security/privacy review.

## 🆘 Support & Contact
- **Security issues**: security@duke.edu
- **Privacy concerns**: privacy@duke.edu
- **General issues**: Create a GitHub issue

## 🏆 Acknowledgments
- Duke University IT Security Team
- Anthropic for Claude AI integration
- Open source security community
- Academic advisors and reviewers

---
**⚠️ Important Security Notice**
This implementation includes production-ready security features but should undergo professional security review before deployment in sensitive environments. Always follow your organization's security policies and compliance requirements.

**🔒 Privacy Notice**
This system is designed with privacy-by-design principles and GDPR compliance in mind. Users have full control over their data with transparent policies and easy deletion options.

**🤖 AI Responsibility Statement**
This AI system includes bias monitoring, content filtering, and transparency features. However, users should always verify important information through official Duke University channels and exercise critical thinking when interacting with AI systems.

## 🚦 Performance Testing & Monitoring

### Load Testing (Locust)

1. Install Locust:
   ```bash
   pip install locust
   ```
2. Run Locust:
   ```bash
   locust -f locustfile.py --host=http://localhost:8501
   ```
3. Open [http://localhost:8089](http://localhost:8089) in your browser to start the test and monitor live results.

### Python Benchmarking (pytest-benchmark)

1. Install pytest-benchmark:
   ```bash
   pip install pytest pytest-benchmark
   ```
2. Run the benchmark:
   ```bash
   pytest tests/test_performance.py --benchmark-only
   ```
   This will show you the average, min, and max response times for your agent.

### Prometheus Monitoring

- Metrics are available at [http://localhost:8000](http://localhost:8000) if enabled in your app.
- Integrate with Prometheus/Grafana for dashboards and alerts.

### Streamlit Logging

- View performance logs in your terminal.
- You can add more detailed logging using Python's `logging` module.
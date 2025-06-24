# Deployment Guide: DukeBot Security Framework

## 1. Prerequisites
- Python 3.11+
- pip package manager
- Git
- AWS Account with Bedrock access
- (Optional) Docker, AWS CLI, kubectl

## 2. Environment Setup

### Clone the Repository
```bash
git clone <repo-url>
```

### Create and Activate Virtual Environment
```bash
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate.bat
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure Environment Variables
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

## 3. Running Locally
```bash
# Activate virtual environment
source venv/bin/activate
# Start the application
streamlit run dukebot/secure_ui.py
```
Open your browser to `http://localhost:8501`

## 4. Docker Deployment

### Build Docker Image
```bash
docker build -t dukebot-secure .
```

### Run Docker Container
```bash
docker run --env-file .env -p 8501:8501 dukebot-secure
```

## 5. Cloud Deployment (AWS Example)
- Use AWS ECS, EKS, or EC2 for deployment.
- Store secrets in AWS Secrets Manager or SSM Parameter Store.
- Use IAM roles for Bedrock access.
- Set environment variables via ECS/EKS task definitions or EC2 user data.
- Use HTTPS (with a load balancer or API Gateway).

## 6. Security & Privacy Best Practices
- Always use HTTPS in production.
- Store secrets securely (never hard-code in code or Docker images).
- Rotate API keys and encryption keys regularly.
- Set strict IAM permissions for AWS resources.
- Enable logging and monitoring for all endpoints.
- Regularly review audit logs and privacy events.
- Run regular security and privacy tests (`pytest`).

## 7. Troubleshooting
- Check `.env` for missing/incorrect keys.
- Review logs in `logs/security_audit.log` for errors.
- Use `pytest` to verify all security/privacy tests pass.

---
For more details, see the technical documentation and user manual in the `doc/` folder. 
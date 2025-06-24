# 🚀 Bedrock Chatbot - Full-Stack AI Application

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Project Overview

**Week 5: Application Development with Bedrock**  
*Develop full-stack applications using Amazon Bedrock, incorporating best practices for production deployments.*

This is a complete **Mini-Project: Full-Stack AI Application** that demonstrates enterprise-grade development practices with AWS Bedrock. The application features a modern web interface, robust backend services, comprehensive authentication system, and real-time monitoring capabilities.

### 🎯 Project Requirements Fulfilled

- ✅ **Frontend Interface**: Modern Streamlit-based web application
- ✅ **Backend Services**: Flask REST API with AWS Bedrock integration
- ✅ **Authentication**: JWT-based user authentication and authorization
- ✅ **Monitoring**: Real-time metrics and system monitoring dashboard
- ✅ **Production Ready**: Docker containerization and security best practices

## 🏗️ Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Frontend      │◄──►│   Backend       │◄──►│   AWS Bedrock   │
│   (Streamlit)   │    │   (Flask API)   │    │   (Claude AI)   │
│   Port: 8501    │    │   Port: 5000    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       
         │                       │                       
         ▼                       ▼                       
┌─────────────────┐    ┌─────────────────┐              
│                 │    │                 │              
│   Session       │    │   SQLite        │              
│   Management    │    │   Database      │              
│                 │    │                 │              
└─────────────────┘    └─────────────────┘              
```

### Technology Stack

#### Frontend
- **Streamlit**: Interactive web application framework
- **Python 3.8+**: Core programming language
- **Requests**: HTTP client for API communication
- **Plotly**: Data visualization and charts

#### Backend
- **Flask**: RESTful API framework
- **AWS Bedrock**: AI/ML model hosting service
- **boto3**: AWS SDK for Python
- **SQLite**: Lightweight database for development
- **JWT**: JSON Web Tokens for authentication
- **bcrypt**: Password hashing and encryption

#### DevOps & Security
- **Docker**: Containerization and deployment
- **Docker Compose**: Multi-container orchestration
- **SSL/TLS**: Secure communications
- **Environment Variables**: Configuration management

## 🚀 Quick Start Guide

### Prerequisites

```bash
# Required software
- Python 3.8 or higher
- Docker and Docker Compose
- AWS Account with Bedrock access
- Git
```

### 1. Clone Repository

```bash
git clone <repository-url>
cd AIPI561/Week2
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env

# Edit environment variables
nano .env
```

Required environment variables:
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# Application Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key
FLASK_ENV=development
DATABASE_URL=sqlite:///app.db

# Security Settings
BCRYPT_LOG_ROUNDS=12
SESSION_TIMEOUT=3600
```

### 3. Quick Deploy with Docker

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Manual Installation

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python app.py
```

#### Frontend Setup
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

### 5. Access Application

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:5001
- **Health Check**: http://localhost:5001/health

### 6. Default Login

```
Username: admin
Password: admin123
```

> ⚠️ **Security Notice**: Change default credentials immediately after first login!

## 📱 Features & Functionality

### 🔐 Authentication System
- **User Registration**: Secure account creation with validation
- **Login/Logout**: JWT-based authentication
- **Password Security**: bcrypt encryption with salt
- **Session Management**: Automatic timeout and security controls
- **Role-Based Access**: User and admin permission levels

### 💬 AI Chat Interface
- **Real-time Chat**: Interactive conversation with Claude AI
- **Context Awareness**: Maintains conversation context
- **Multiple Models**: Support for different Claude models
- **Message History**: Persistent conversation storage
- **Error Handling**: Graceful failure recovery

### 📊 Monitoring Dashboard
- **Real-time Metrics**: Live system performance data
- **API Usage Statistics**: Request counts and response times
- **User Activity**: Login patterns and usage analytics
- **System Health**: Service status and error monitoring
- **Visual Charts**: Interactive Plotly visualizations

### 🛡️ Security Features
- **Multi-layer Security**: Network, application, and data protection
- **Input Validation**: SQL injection and XSS prevention
- **Rate Limiting**: API abuse protection
- **Audit Logging**: Comprehensive security event tracking
- **Container Security**: Non-root user execution

## 📁 Project Structure

```
AIPI561/Week9/
├── 📁 backend/                 # Backend services
│   ├── app.py                 # Flask application entry
│   ├── auth.py                # Authentication logic
│   ├── bedrock_api.py         # AWS Bedrock integration
│   ├── metrics.py             # Monitoring metrics
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container config
├── 📁 frontend/               # Frontend application
│   ├── app.py                # Streamlit main app
│   ├── components/           # UI components
│   │   ├── auth.py          # Auth components
│   │   ├── chat.py          # Chat interface
│   │   └── dashboard.py     # Monitoring dashboard
│   ├── requirements.txt      # Frontend dependencies
│   └── Dockerfile           # Frontend container config
├── 📁 docs/                  # Documentation
│   ├── architecture.md      # 🏗️ System architecture
│   ├── user_guide.md        # 📖 User guide
│   └── security.md          # 🔒 Security documentation
├── 📁 scripts/               # Utility scripts
│   ├── start_backend.sh     # Backend startup
│   ├── start_frontend.sh    # Frontend startup
│   └── setup.sh            # Environment setup
├── docker-compose.yml       # Multi-container setup
├── .env.example             # Environment template
└── README.md               # This file
```

## 🔧 Development Guide

### Local Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run backend in development mode
cd backend
export FLASK_ENV=development
python app.py

# Run frontend with hot reload
cd frontend
streamlit run app.py --server.runOnSave true
```

### Testing

```bash
# Run backend tests
cd backend
python -m pytest tests/

# Run frontend tests
cd frontend
python -m pytest tests/

# Integration tests
python -m pytest integration_tests/
```

### Code Quality

```bash
# Linting
flake8 backend/ frontend/

# Type checking
mypy backend/ frontend/

# Security scanning
bandit -r backend/ frontend/
```

## 🚢 Deployment

### Production Deployment

1. **Environment Configuration**
```bash
# Production environment variables
export FLASK_ENV=production
export JWT_SECRET_KEY="production-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

2. **SSL Certificate Setup**
```bash
# Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

3. **Production Docker Compose**
```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d
```

### Health Checks

```bash
# Backend health
curl http://localhost:5001/health

# Frontend status
curl http://localhost:8501/_stcore/health
```

## 📊 Monitoring & Metrics

### Available Metrics

- **API Performance**: Response times, throughput, error rates
- **User Activity**: Active users, session duration, feature usage
- **System Resources**: CPU, memory, disk usage
- **Security Events**: Failed logins, suspicious activities
- **Business Metrics**: Chat interactions, model usage

### Monitoring Endpoints

```bash
# Metrics endpoint
GET /api/metrics

# Health check
GET /health

# System status
GET /api/status
```

## 🔒 Security

### Security Features

- **Authentication**: JWT tokens with expiration
- **Authorization**: Role-based access control
- **Data Protection**: Encrypted sensitive data
- **Network Security**: HTTPS/TLS encryption
- **Container Security**: Non-root user execution
- **Input Validation**: XSS and injection prevention

### Security Best Practices

1. **Regular Updates**: Keep dependencies updated
2. **Access Control**: Implement least privilege principle
3. **Monitoring**: Enable comprehensive logging
4. **Backup Strategy**: Regular data backups
5. **Incident Response**: Defined security procedures

For detailed security information, see [`docs/security.md`](docs/security.md).

## 📚 Documentation

### 📖 Deliverables

This project includes all required deliverables:

1. **✅ Complete Application**
   - Full-stack implementation with frontend and backend
   - AWS Bedrock integration for AI capabilities
   - Production-ready containerization

2. **✅ Architecture Document** → [`docs/architecture.md`](docs/architecture.md)
   - System overview and component design
   - Technology stack and integration details
   - Deployment and scaling strategies

3. **✅ User Guide** → [`docs/user_guide.md`](docs/user_guide.md)
   - Step-by-step usage instructions
   - Feature explanations and best practices
   - Troubleshooting and FAQ

4. **✅ Security Documentation** → [`docs/security.md`](docs/security.md)
   - Multi-layer security architecture
   - Threat model and risk assessment
   - Security configuration checklist

### Additional Resources

- **API Documentation**: Detailed endpoint specifications
- **Development Guide**: Setup and contribution guidelines
- **Deployment Guide**: Production deployment strategies
- **Troubleshooting**: Common issues and solutions

## 📋 API Reference

### Authentication Endpoints

```bash
POST /api/auth/register    # User registration
POST /api/auth/login       # User login
POST /api/auth/logout      # User logout
GET  /api/auth/profile     # User profile
```

### Chat Endpoints

```bash
POST /api/chat/message     # Send chat message
GET  /api/chat/history     # Get chat history
DELETE /api/chat/clear     # Clear chat history
```

### Monitoring Endpoints

```bash
GET /api/metrics           # System metrics
GET /api/metrics/users     # User metrics
GET /api/health           # Health check
```

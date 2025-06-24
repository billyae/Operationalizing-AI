# 📖 User Guide

## Overview

Welcome to the Bedrock Chatbot enterprise-grade AI chat application! This guide will help you quickly get started with all the features of the system.

## Quick Start

### System Access

1. **Open your browser** and access the application URL:
   - Development environment: `http://localhost:8501`
   - Production environment: Access according to the deployed domain configuration

2. **System Requirements**:
   - Modern browser (Chrome, Firefox, Safari, Edge)
   - Stable internet connection
   - JavaScript enabled

### First Login

#### Using Default Admin Account

1. On the login page, enter:
   - **Username**: `admin`
   - **Password**: `admin123`

2. Click the "Login" button

3. **Important**: After first login, it is strongly recommended to immediately change the default password

## Main Features

### 1. User Authentication System

#### Login Function

**Step-by-step Instructions:**
1. Select "Login" option on the homepage
2. Enter valid username and password
3. Click the "Login" button
4. Automatically redirected to chat interface upon success

**Notes:**
- Password is case-sensitive
- Login failures will display error messages

#### User Registration

**New User Registration Process:**
1. Click "Register New Account" on the login page
2. Fill in registration information:
   - **Username**: 3-20 characters, alphanumeric combination
   - **Password**: At least 6 characters, recommended to include numbers and special characters
   - **Email**: Valid email address (optional)
3. Click "Register" button
4. Return to login page after successful registration

**Password Requirements:**
- Minimum 6 characters
- Recommended to include uppercase letters, lowercase letters, numbers, and special characters
- Avoid common passwords (e.g., 123456, password, etc.)

### 2. AI Chat Function

#### Basic Chat Operations

**Sending Messages:**
1. Enter the chat interface after successful login
2. Type your question or message in the input box at the bottom
3. Press `Enter` key or click "Send" button
4. Wait for AI response (usually 2-10 seconds)

**Chat Features:**
- ✅ Supports Chinese and English conversations
- ✅ Context understanding capability
- ✅ Real-time responses
- ✅ Conversation history saving
- ✅ Error handling and retry

#### Chat Tips

**Effective Question Formats:**

1. **Specific and Clear Questions**
   ```
   ❌ Poor question: Help me write code
   ✅ Good question: Help me write a Python function to calculate the greatest common divisor of two numbers
   ```

2. **Provide Background Information**
   ```
   ❌ Poor question: How to solve this error?
   ✅ Good question: I encountered "ImportError: No module named 'flask'" when running my Flask application. How should I resolve this?
   ```

3. **Step-by-step Inquiries**
   ```
   ✅ Good question: Please help me explain step-by-step how to deploy a Docker application:
   1. First, how to build an image?
   2. Then, how to run a container?
   3. Finally, how to configure port mapping?
   ```

#### Conversation Management

**View Conversation History:**
- All conversations in the current session are automatically saved
- Scroll through the page to view historical messages
- Support copying AI reply content

**Clear Conversation History:**
- Click "Clear History" button
- Clear current session records after confirmation
- New conversations will start fresh

**Session Persistence:**
- Conversation history remains after page refresh
- Session history is cleared after re-login
- Important conversations should be saved promptly

### 3. Monitoring Dashboard

#### Accessing Monitoring Features

1. Select "Monitoring Panel" in the sidebar after login
2. View real-time system metrics and usage statistics

#### Monitoring Metrics Explanation

**API Call Statistics:**
- **Total Calls**: Cumulative number of requests processed by the system
- **Success Rate**: Percentage of successfully processed requests
- **Average Response Time**: Average time taken for AI responses
- **Error Rate**: Percentage of failed requests

**Usage Analysis:**
- **Daily Call Trends**: Shows recent usage patterns
- **Popular Models**: Statistics of most frequently used AI models
- **User Activity**: User login and usage frequency

**System Performance:**
- **Real-time Response Status**: Current system health status
- **Resource Usage**: Memory, CPU, and other resource consumption
- **Database Status**: Data storage and query performance

### 4. Account Management

#### Personal Information View

1. Click username in the top right corner
2. Select "Personal Information"
3. View account details:
   - Username
   - Registration time
   - Last login time
   - Account status

#### Password Change

**Secure Password Change Process:**
1. Go to personal information page
2. Click "Change Password"
3. Enter current password
4. Enter new password (confirm twice)
5. Click "Confirm Changes"

**Password Security Recommendations:**
- Change passwords regularly (recommended every 3-6 months)
- Use strong password combinations
- Don't use the same password as other systems
- Avoid changing passwords in public places

#### System Logout

**Secure Logout:**
1. Click username in the top right corner
2. Select "Logout"
3. Clear local session information after confirmation

**Automatic Logout Scenarios:**
- Session automatically expires after 24 hours
- Automatic logout after prolonged inactivity
- Logout when system detects abnormal activity

## Advanced Features

### 1. Batch Conversation Processing

**Applicable Scenarios:**
- Need to process multiple related questions
- Batch document analysis
- Batch code review

**Operation Method:**
1. Prepare list of questions to process
2. Send to AI one by one
3. Collect and organize AI replies
4. Export or save results

### 2. Custom Prompts

**Prompt Optimization Tips:**

**Role Setting:**
```
You are an experienced software architect. Please help me analyze this system design proposal...
```

**Format Requirements:**
```
Please organize the following information in table format, including: functional modules, technology stack, responsible person, completion time
```

**Thinking Steps:**
```
Please analyze this problem step by step:
1. First identify core requirements
2. Then analyze technology selection
3. Finally provide implementation suggestions
```

### 3. Error Handling and Troubleshooting

#### Common Issues and Solutions

**Login Issues:**

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Cannot login | Incorrect username or password | Check input, pay attention to case sensitivity |
| Login timeout | Network connection issues | Check network, refresh page and retry |
| Session expired | No activity for over 24 hours | Login again |

**Chat Function Issues:**

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| AI no response | Backend service exception | Try again later, contact administrator |
| Slow response | Network delay or high load | Wait patiently, avoid duplicate sending |
| Garbled display | Encoding issues | Refresh page, check browser settings |

**Page Display Issues:**

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Blank page | JavaScript error | Check browser console, enable JS |
| Style confusion | CSS loading failure | Clear browser cache |
| Non-functional buttons | Insufficient permissions | Check login status, login again |

## Best Practices

### 1. Security Usage Guide

**Account Security:**
- ✅ Use strong passwords and change regularly
- ✅ Don't share account information
- ✅ Logout promptly
- ✅ Regularly check account activity

**Data Security:**
- ✅ Don't input sensitive personal information
- ✅ Avoid uploading confidential documents
- ✅ Pay attention to conversation content privacy
- ✅ Backup important information promptly

### 2. Efficient Usage Tips

**Question Techniques:**
1. **Clear Goals**: Clearly express what you want
2. **Provide Context**: Give necessary background information
3. **Break Down Complex Questions**: Split large questions into smaller ones
4. **Verify Results**: Perform necessary verification of AI replies

**Time Management:**
- Plan usage time reasonably
- Avoid over-reliance on AI
- Combine AI suggestions with human judgment
- Maintain habits of learning and thinking

### 3. Collaborative Usage Guide

**Team Collaboration:**
- Establish team usage standards
- Share effective prompt templates
- Organize common conversation patterns
- Regularly summarize usage experience

**Knowledge Management:**
- Save important conversation records
- Build personal knowledge base
- Categorize and organize AI replies
- Continuously optimize questioning methods

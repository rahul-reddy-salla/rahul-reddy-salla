# Email Access Request Agent 🤖

A Langchain-based intelligent agent that automatically processes email access requests with human-in-the-loop approval and MCP (Model Context Protocol) tool calling for access provisioning.

## 🌟 Features

- **📧 Email Reading**: Connects to email servers (IMAP) to read and monitor incoming emails
- **🔍 AI-Powered Detection**: Uses Langchain and LLMs to intelligently detect and parse access requests from email content
- **👤 Human-in-the-Loop**: Notifies humans and waits for approval before granting access
- **🔧 MCP Tool Calling**: Uses Model Context Protocol to provision access to various systems
- **📊 Audit Trail**: Maintains complete history of approvals and provisioned access
- **🎯 Flexible**: Works with multiple LLM providers (OpenAI, Anthropic) and supports demo mode

## 🏗️ Architecture

```
┌─────────────┐
│   Emails    │
│  (IMAP/Demo)│
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│   Email Reader          │
│  (email_reader.py)      │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Access Detector        │
│  (Langchain + LLM)      │
│  (access_detector.py)   │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Approval Manager       │
│  (Human-in-the-Loop)    │
│  (approval_manager.py)  │
└──────────┬──────────────┘
           │ (after approval)
           ▼
┌─────────────────────────┐
│  MCP Manager            │
│  (Tool Calling)         │
│  (mcp_manager.py)       │
└─────────────────────────┘
```

## 📋 Requirements

- Python 3.8+
- Langchain
- An LLM API key (OpenAI or Anthropic)
- (Optional) Email credentials for live email monitoring
- (Optional) MCP client for actual access provisioning

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/rahul-reddy-salla/rahul-reddy-salla.git
cd rahul-reddy-salla
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## ⚙️ Configuration

Edit `.env` file with your settings:

```env
# LLM Configuration (required)
OPENAI_API_KEY=your-openai-api-key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# Email Configuration (optional - runs in demo mode without these)
EMAIL_ADDRESS=your-email@example.com
EMAIL_PASSWORD=your-app-specific-password
IMAP_SERVER=imap.gmail.com

# Agent Configuration
NOTIFICATION_METHOD=console
```

## 💻 Usage

### Basic Example

```python
from langchain_openai import ChatOpenAI
from email_access_agent.agent import EmailAccessAgent

# Initialize LLM
llm = ChatOpenAI(model="gpt-4", temperature=0)

# Create agent (demo mode without email credentials)
agent = EmailAccessAgent(llm=llm)

# Process emails and detect access requests
result = agent.process_emails()
print(f"Found {result['access_requests_found']} access requests")

# View pending requests
pending = agent.get_pending_requests()
for req in pending:
    print(f"Request from {req['requester']} for {req['resource']}")

# Approve a request (triggers MCP tool calling)
agent.approve_request(
    request_id="abc123",
    approver="admin@company.com",
    comments="Approved - valid business need"
)

# Or reject a request
agent.reject_request(
    request_id="xyz789",
    approver="admin@company.com",
    comments="Insufficient justification"
)
```

### Run the Demo

```bash
python example_usage.py
```

This will:
1. Process sample emails (or connect to your email if configured)
2. Detect access requests using AI
3. Display pending approvals
4. Automatically approve one request (for demo)
5. Simulate MCP tool calling to provision access
6. Show provisioning history

### Interactive Mode

```bash
python interactive_demo.py
```

This provides an interactive CLI where you can:
- Process emails manually
- View pending requests
- Approve/reject requests interactively
- View provisioning history

## 📁 Project Structure

```
.
├── email_access_agent/
│   ├── __init__.py           # Package initialization
│   ├── agent.py              # Main orchestration agent
│   ├── email_reader.py       # Email reading functionality
│   ├── access_detector.py    # AI-powered access request detection
│   ├── approval_manager.py   # Human approval workflow
│   └── mcp_manager.py        # MCP tool calling for provisioning
├── example_usage.py          # Basic usage example
├── interactive_demo.py       # Interactive CLI demo
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## 🔍 How It Works

### 1. Email Reading
The agent connects to an email server (or uses demo data) and retrieves unread emails.

### 2. Access Request Detection
Using Langchain and LLMs, the agent analyzes email content to detect access requests. It extracts:
- Requester name/email
- Resource being requested
- Type of access needed
- Justification
- Urgency level

### 3. Human-in-the-Loop Approval
When an access request is detected, the agent:
- Creates an approval request
- Notifies a human (via console, email, Slack, etc.)
- Waits for approval or rejection

### 4. Access Provisioning
Upon approval, the agent:
- Calls appropriate MCP tools based on the resource type
- Provisions the requested access
- Records the transaction in audit history

## 🛠️ MCP Tool Integration

The agent automatically selects and calls MCP tools based on the resource type:

- `grant_database_access` - For database access requests
- `grant_aws_access` - For AWS/S3/EC2 access
- `grant_github_access` - For GitHub repository access
- `grant_jira_access` - For Jira project access
- `grant_slack_access` - For Slack workspace access
- `grant_generic_access` - For other resources

Currently runs in simulation mode. To integrate with actual MCP:

```python
from your_mcp_client import MCPClient

mcp_client = MCPClient(endpoint="...", api_key="...")
agent = EmailAccessAgent(llm=llm, mcp_client=mcp_client)
```

## 🔐 Security Considerations

- **Email Credentials**: Use app-specific passwords, not your main password
- **API Keys**: Store in `.env` file (never commit to git)
- **Approval Required**: All access requires human approval before provisioning
- **Audit Trail**: Complete history of all requests and provisioning
- **Access Types**: Granular control over read/write/admin permissions

## 🎨 Customization

### Custom Notification Methods

```python
# Extend ApprovalManager to add custom notification
class CustomApprovalManager(ApprovalManager):
    def _notify_human(self, approval_req):
        # Your custom notification logic (Slack, email, webhook, etc.)
        pass
```

### Custom MCP Tools

```python
# Extend MCPAccessManager to add custom tool mapping
class CustomMCPManager(MCPAccessManager):
    def _select_tool(self, resource):
        # Your custom tool selection logic
        return "your_custom_tool"
```

## 📊 Example Output

```
================================================================================
🔔 NEW ACCESS REQUEST REQUIRES APPROVAL
================================================================================
Request ID: a7b2c9d1
Requester: john.doe@company.com
Resource: Production Database
Access Type: read
Urgency: high

Justification:
  I need read access to the production database for the customer support 
  dashboard project.

Original Email:
  From: john.doe@company.com
  Subject: Access Request: Production Database
  Date: Mon, 6 Jan 2026 10:30:00 -0800
================================================================================
```

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:
- Additional notification methods (Slack, Microsoft Teams)
- More sophisticated access detection logic
- Integration with actual MCP servers
- Support for more email providers
- Batch approval workflows
- Web UI for approval management

## 📄 License

MIT License - feel free to use this in your projects!

## 👤 Author

**Rahul Reddy Salla**
- GitHub: [@rahul-reddy-salla](https://github.com/rahul-reddy-salla)

---

⭐ If you find this project useful, please consider giving it a star!

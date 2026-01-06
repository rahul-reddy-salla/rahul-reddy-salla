"""
Example usage of the Email Access Agent
Demonstrates the workflow: email reading -> access detection -> approval -> provisioning
"""

import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from email_access_agent.agent import EmailAccessAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main example demonstrating the email access agent"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize LLM (choose based on your preference)
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    
    if llm_provider == "openai":
        llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4"),
            temperature=0
        )
    elif llm_provider == "anthropic":
        llm = ChatAnthropic(
            model=os.getenv("LLM_MODEL", "claude-3-opus-20240229"),
            temperature=0
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")
    
    # Initialize the agent
    # Note: If EMAIL_ADDRESS is not set, agent runs in demo mode with sample emails
    agent = EmailAccessAgent(
        llm=llm,
        email_address=os.getenv("EMAIL_ADDRESS"),
        email_password=os.getenv("EMAIL_PASSWORD"),
        imap_server=os.getenv("IMAP_SERVER", "imap.gmail.com"),
        notification_method=os.getenv("NOTIFICATION_METHOD", "console")
    )
    
    print("\n" + "="*80)
    print("Email Access Request Agent - Demo")
    print("="*80 + "\n")
    
    # Connect to email if credentials provided
    if os.getenv("EMAIL_ADDRESS"):
        logger.info("Connecting to email server...")
        if agent.connect_email():
            logger.info("Successfully connected to email")
        else:
            logger.error("Failed to connect to email, running in demo mode")
    else:
        logger.info("No email credentials provided, running in DEMO MODE")
        logger.info("Using sample emails to demonstrate workflow")
    
    # Process emails and detect access requests
    print("\n📧 Step 1: Processing emails and detecting access requests...\n")
    result = agent.process_emails(limit=10)
    
    if result["success"]:
        print(f"✅ Processed {result['emails_processed']} emails")
        print(f"✅ Found {result['access_requests_found']} access requests")
        print(f"✅ Created {result['approvals_pending']} approval requests")
        
        if result["access_requests_found"] > 0:
            print(f"\n📋 Approval Request IDs: {', '.join(result['approval_ids'])}")
    else:
        print(f"❌ Error: {result.get('error')}")
        return
    
    # Show pending requests
    print("\n📋 Step 2: Reviewing pending approval requests...\n")
    pending = agent.get_pending_requests()
    
    if not pending:
        print("No pending requests at this time.")
        return
    
    for i, req in enumerate(pending, 1):
        print(f"\nRequest #{i}:")
        print(f"  ID: {req['request_id']}")
        print(f"  Requester: {req['requester']}")
        print(f"  Resource: {req['resource']}")
        print(f"  Access Type: {req['access_type']}")
        print(f"  Urgency: {req['urgency']}")
    
    # Interactive approval (demo)
    print("\n" + "="*80)
    print("🎯 Step 3: Human-in-the-Loop Approval")
    print("="*80)
    print("\nIn a production system, a human would review and approve/reject requests.")
    print("For this demo, we'll automatically approve the first request.\n")
    
    if pending:
        first_request_id = pending[0]["request_id"]
        
        # Approve the first request
        print(f"✅ Approving request {first_request_id}...\n")
        approval_result = agent.approve_request(
            request_id=first_request_id,
            approver="admin@company.com",
            comments="Approved for demo purposes"
        )
        
        if approval_result["success"]:
            print("✅ Request approved successfully!")
            print("\n🔧 Step 4: Provisioning access via MCP tool calling...")
            
            prov_result = approval_result["provisioning_result"]
            if prov_result.get("success"):
                print("\n✅ ACCESS PROVISIONED SUCCESSFULLY!")
                print(f"\nProvisioning Details:")
                print(f"  Tool: {prov_result.get('tool_name', 'N/A')}")
                print(f"  Message: {prov_result.get('message', 'N/A')}")
                
                if prov_result.get("simulation"):
                    print("\n⚠️  NOTE: Running in simulation mode (no actual access granted)")
                
                if "access_details" in prov_result:
                    details = prov_result["access_details"]
                    print(f"\nAccess Details:")
                    print(f"  User: {details.get('user')}")
                    print(f"  Resource: {details.get('resource')}")
                    print(f"  Permissions: {', '.join(details.get('permissions', []))}")
                    print(f"  Granted By: {details.get('granted_by')}")
            else:
                print(f"❌ Provisioning failed: {prov_result.get('error')}")
        else:
            print(f"❌ Approval failed: {approval_result.get('error')}")
    
    # Show provisioning history
    print("\n📊 Step 5: Provisioning History")
    print("="*80 + "\n")
    
    history = agent.get_provisioning_history()
    if history:
        for i, entry in enumerate(history, 1):
            print(f"\nProvisioning #{i}:")
            print(f"  Status: {entry['status']}")
            print(f"  Tool: {entry['tool_name']}")
            print(f"  User: {entry['tool_args']['user']}")
            print(f"  Resource: {entry['tool_args']['resource']}")
    else:
        print("No provisioning history yet.")
    
    # Disconnect from email
    if os.getenv("EMAIL_ADDRESS"):
        agent.disconnect_email()
    
    print("\n" + "="*80)
    print("✅ Demo completed successfully!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

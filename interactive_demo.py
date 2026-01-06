"""
Interactive demo script for the Email Access Agent
Allows manual approval/rejection of requests
"""

import os
import sys
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from email_access_agent.agent import EmailAccessAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def display_menu():
    """Display the interactive menu"""
    print("\n" + "="*80)
    print("Email Access Agent - Interactive Mode")
    print("="*80)
    print("\nOptions:")
    print("  1. Process new emails")
    print("  2. View pending requests")
    print("  3. Approve a request")
    print("  4. Reject a request")
    print("  5. View provisioning history")
    print("  6. Exit")
    print("\n" + "="*80)


def main():
    """Interactive demo"""
    load_dotenv()
    
    # Initialize LLM
    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4"),
        temperature=0
    )
    
    # Initialize agent
    agent = EmailAccessAgent(
        llm=llm,
        email_address=os.getenv("EMAIL_ADDRESS"),
        email_password=os.getenv("EMAIL_PASSWORD"),
        notification_method="console"
    )
    
    print("\n🚀 Starting Email Access Agent (Interactive Mode)")
    
    if os.getenv("EMAIL_ADDRESS"):
        if agent.connect_email():
            print("✅ Connected to email server")
        else:
            print("⚠️  Failed to connect, running in demo mode")
    else:
        print("⚠️  No email configured, running in demo mode")
    
    while True:
        display_menu()
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            print("\n📧 Processing emails...")
            result = agent.process_emails()
            print(f"\n✅ Processed {result['emails_processed']} emails")
            print(f"✅ Found {result['access_requests_found']} access requests")
            
        elif choice == "2":
            print("\n📋 Pending Requests:")
            pending = agent.get_pending_requests()
            if not pending:
                print("  No pending requests")
            else:
                for req in pending:
                    print(f"\n  ID: {req['request_id']}")
                    print(f"  Requester: {req['requester']}")
                    print(f"  Resource: {req['resource']}")
                    print(f"  Access Type: {req['access_type']}")
                    print(f"  Urgency: {req['urgency']}")
                    
        elif choice == "3":
            request_id = input("\nEnter request ID to approve: ").strip()
            approver = input("Enter your name/email: ").strip()
            comments = input("Comments (optional): ").strip()
            
            result = agent.approve_request(request_id, approver, comments or None)
            if result["success"]:
                print("\n✅ Request approved and access provisioned!")
            else:
                print(f"\n❌ Error: {result.get('error')}")
                
        elif choice == "4":
            request_id = input("\nEnter request ID to reject: ").strip()
            approver = input("Enter your name/email: ").strip()
            comments = input("Reason for rejection: ").strip()
            
            result = agent.reject_request(request_id, approver, comments)
            if result["success"]:
                print("\n✅ Request rejected")
            else:
                print(f"\n❌ Error: {result.get('error')}")
                
        elif choice == "5":
            print("\n📊 Provisioning History:")
            history = agent.get_provisioning_history()
            if not history:
                print("  No history yet")
            else:
                for i, entry in enumerate(history, 1):
                    print(f"\n  #{i}: {entry['status'].upper()}")
                    print(f"    User: {entry['tool_args']['user']}")
                    print(f"    Resource: {entry['tool_args']['resource']}")
                    
        elif choice == "6":
            print("\n👋 Goodbye!")
            agent.disconnect_email()
            sys.exit(0)
            
        else:
            print("\n❌ Invalid choice, please try again")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user, exiting...")
        sys.exit(0)

"""
Main Email Access Agent
Orchestrates the entire workflow: reading emails, detecting requests, 
getting approval, and provisioning access
"""

from typing import Dict, List, Optional
import logging
from uuid import uuid4

from .email_reader import EmailReader
from .access_detector import AccessRequestDetector
from .approval_manager import ApprovalManager
from .mcp_manager import MCPAccessManager

logger = logging.getLogger(__name__)


class EmailAccessAgent:
    """
    Main agent that orchestrates the email access request workflow
    """
    
    def __init__(
        self,
        llm,
        email_address: Optional[str] = None,
        email_password: Optional[str] = None,
        imap_server: str = "imap.gmail.com",
        mcp_client=None,
        notification_method: str = "console"
    ):
        """
        Initialize the email access agent
        
        Args:
            llm: Langchain LLM instance for access detection
            email_address: Email address to monitor (optional for demo mode)
            email_password: Email password (optional for demo mode)
            imap_server: IMAP server address
            mcp_client: MCP client for tool calling (optional, will simulate if not provided)
            notification_method: How to notify humans (console, email, slack)
        """
        self.llm = llm
        
        # Initialize components
        self.email_reader = EmailReader(email_address, email_password, imap_server) if email_address else None
        self.access_detector = AccessRequestDetector(llm)
        self.approval_manager = ApprovalManager(notification_method)
        self.mcp_manager = MCPAccessManager(mcp_client)
        
        self.is_connected = False
    
    def connect_email(self) -> bool:
        """
        Connect to email server
        
        Returns:
            True if successful, False otherwise
        """
        if not self.email_reader:
            logger.warning("Email reader not configured, running in demo mode")
            return False
        
        self.is_connected = self.email_reader.connect()
        return self.is_connected
    
    def disconnect_email(self):
        """Disconnect from email server"""
        if self.email_reader:
            self.email_reader.disconnect()
            self.is_connected = False
    
    def process_emails(self, limit: int = 10) -> Dict:
        """
        Process unread emails looking for access requests
        
        Args:
            limit: Maximum number of emails to process
            
        Returns:
            Summary of processing results
        """
        if not self.is_connected and self.email_reader:
            logger.error("Not connected to email server. Call connect_email() first.")
            return {
                "success": False,
                "error": "Not connected to email server"
            }
        
        # Get unread emails (or use demo data if no email reader)
        if self.email_reader:
            emails = self.email_reader.get_unread_emails(limit=limit)
        else:
            logger.info("Running in demo mode with sample emails")
            emails = self._get_demo_emails()
        
        if not emails:
            logger.info("No emails to process")
            return {
                "success": True,
                "emails_processed": 0,
                "access_requests_found": 0,
                "approvals_pending": 0
            }
        
        # Detect access requests
        access_requests = self.access_detector.batch_detect(emails)
        
        # Create approval requests for each access request found
        approvals_created = []
        for email_data, access_request in access_requests:
            request_id = str(uuid4())[:8]
            approval_req = self.approval_manager.request_approval(
                request_id, access_request, email_data
            )
            approvals_created.append(request_id)
        
        return {
            "success": True,
            "emails_processed": len(emails),
            "access_requests_found": len(access_requests),
            "approvals_pending": len(approvals_created),
            "approval_ids": approvals_created
        }
    
    def approve_request(self, request_id: str, approver: str, comments: Optional[str] = None) -> Dict:
        """
        Approve an access request and provision access
        
        Args:
            request_id: ID of the request to approve
            approver: Name/ID of the person approving
            comments: Optional comments
            
        Returns:
            Result of approval and provisioning
        """
        # Get the request
        approval_req = self.approval_manager.get_request(request_id)
        if not approval_req:
            return {
                "success": False,
                "error": f"Request {request_id} not found"
            }
        
        # Approve the request
        success = self.approval_manager.approve_request(request_id, approver, comments)
        if not success:
            return {
                "success": False,
                "error": "Failed to approve request"
            }
        
        # Provision the access via MCP
        approval_data = {
            "approver": approver,
            "comments": comments
        }
        
        provisioning_result = self.mcp_manager.provision_access(
            approval_req.access_request,
            approval_data
        )
        
        logger.info(f"Request {request_id} approved and access provisioned")
        
        return {
            "success": True,
            "request_id": request_id,
            "approval_status": "approved",
            "provisioning_result": provisioning_result
        }
    
    def reject_request(self, request_id: str, approver: str, comments: Optional[str] = None) -> Dict:
        """
        Reject an access request
        
        Args:
            request_id: ID of the request to reject
            approver: Name/ID of the person rejecting
            comments: Optional comments explaining rejection
            
        Returns:
            Result of rejection
        """
        success = self.approval_manager.reject_request(request_id, approver, comments)
        
        if success:
            logger.info(f"Request {request_id} rejected by {approver}")
            return {
                "success": True,
                "request_id": request_id,
                "approval_status": "rejected",
                "message": f"Request rejected: {comments or 'No reason provided'}"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to reject request {request_id}"
            }
    
    def get_pending_requests(self) -> List[Dict]:
        """
        Get all pending approval requests
        
        Returns:
            List of pending request dictionaries
        """
        pending = self.approval_manager.get_pending_requests()
        return [req.to_dict() for req in pending.values()]
    
    def get_provisioning_history(self) -> List[Dict]:
        """Get history of provisioned access"""
        return self.mcp_manager.get_provisioning_history()
    
    def _get_demo_emails(self) -> List[Dict]:
        """
        Generate demo emails for testing without email server
        
        Returns:
            List of sample email dictionaries
        """
        return [
            {
                "id": "demo-001",
                "subject": "Access Request: Production Database",
                "from": "john.doe@company.com",
                "date": "Mon, 6 Jan 2026 10:30:00 -0800",
                "body": """Hi Team,

I need read access to the production database for the customer support dashboard project. 
I'll be working on some analytics queries to help improve our customer service response times.

This is needed by end of week for the quarterly review.

Thanks,
John Doe
Customer Support Team"""
            },
            {
                "id": "demo-002",
                "subject": "Urgent: AWS S3 Access Needed",
                "from": "jane.smith@company.com",
                "date": "Mon, 6 Jan 2026 11:45:00 -0800",
                "body": """Hello,

I urgently need write access to the s3://company-data-backup bucket to restore some 
accidentally deleted files. This is blocking the entire marketing team from accessing 
their campaign data.

Can someone please grant me access ASAP? This is critical.

Best regards,
Jane Smith
Marketing Operations"""
            },
            {
                "id": "demo-003",
                "subject": "Meeting reminder for tomorrow",
                "from": "bob.wilson@company.com",
                "date": "Mon, 6 Jan 2026 14:20:00 -0800",
                "body": """Hey everyone,

Just a reminder that we have our weekly standup tomorrow at 10 AM.

See you there!
Bob"""
            }
        ]
    
    def run_continuous(self, interval: int = 300):
        """
        Run the agent continuously, checking for emails at regular intervals
        
        Args:
            interval: Time between checks in seconds (default: 5 minutes)
        """
        import time
        
        logger.info(f"Starting continuous monitoring (checking every {interval} seconds)")
        
        try:
            while True:
                logger.info("Checking for new emails...")
                result = self.process_emails()
                
                if result["success"]:
                    logger.info(f"Processed {result['emails_processed']} emails, "
                              f"found {result['access_requests_found']} access requests")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Stopping continuous monitoring")
            self.disconnect_email()

"""
Human-in-the-Loop Approval Manager
Handles requesting and tracking approvals from humans
"""

from typing import Dict, Optional
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Status of an approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalRequest:
    """Represents an approval request"""
    
    def __init__(self, request_id: str, access_request, email_data: Dict):
        """
        Initialize approval request
        
        Args:
            request_id: Unique ID for this approval request
            access_request: AccessRequest object
            email_data: Original email data
        """
        self.request_id = request_id
        self.access_request = access_request
        self.email_data = email_data
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now()
        self.resolved_at = None
        self.approver = None
        self.comments = None
    
    def approve(self, approver: str, comments: Optional[str] = None):
        """Mark as approved"""
        self.status = ApprovalStatus.APPROVED
        self.resolved_at = datetime.now()
        self.approver = approver
        self.comments = comments
        logger.info(f"Request {self.request_id} approved by {approver}")
    
    def reject(self, approver: str, comments: Optional[str] = None):
        """Mark as rejected"""
        self.status = ApprovalStatus.REJECTED
        self.resolved_at = datetime.now()
        self.approver = approver
        self.comments = comments
        logger.info(f"Request {self.request_id} rejected by {approver}")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for display"""
        return {
            "request_id": self.request_id,
            "requester": self.access_request.requester,
            "resource": self.access_request.resource,
            "access_type": self.access_request.access_type,
            "justification": self.access_request.justification,
            "urgency": self.access_request.urgency,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "email_subject": self.email_data.get("subject", ""),
            "email_from": self.email_data.get("from", "")
        }


class ApprovalManager:
    """
    Manages approval workflow for access requests
    """
    
    def __init__(self, notification_method: str = "console"):
        """
        Initialize approval manager
        
        Args:
            notification_method: How to notify humans (console, email, slack, webhook)
        """
        self.notification_method = notification_method
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.completed_requests: Dict[str, ApprovalRequest] = {}
    
    def request_approval(self, request_id: str, access_request, email_data: Dict) -> ApprovalRequest:
        """
        Create and submit an approval request to a human
        
        Args:
            request_id: Unique ID for this request
            access_request: AccessRequest object
            email_data: Original email data
            
        Returns:
            ApprovalRequest object
        """
        approval_req = ApprovalRequest(request_id, access_request, email_data)
        self.pending_requests[request_id] = approval_req
        
        # Notify human
        self._notify_human(approval_req)
        
        return approval_req
    
    def get_pending_requests(self) -> Dict[str, ApprovalRequest]:
        """Get all pending approval requests"""
        return self.pending_requests.copy()
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific request by ID"""
        if request_id in self.pending_requests:
            return self.pending_requests[request_id]
        elif request_id in self.completed_requests:
            return self.completed_requests[request_id]
        return None
    
    def approve_request(self, request_id: str, approver: str, comments: Optional[str] = None) -> bool:
        """
        Approve a pending request
        
        Args:
            request_id: ID of request to approve
            approver: Name/ID of person approving
            comments: Optional approval comments
            
        Returns:
            True if successful, False otherwise
        """
        if request_id not in self.pending_requests:
            logger.error(f"Request {request_id} not found in pending requests")
            return False
        
        approval_req = self.pending_requests.pop(request_id)
        approval_req.approve(approver, comments)
        self.completed_requests[request_id] = approval_req
        
        return True
    
    def reject_request(self, request_id: str, approver: str, comments: Optional[str] = None) -> bool:
        """
        Reject a pending request
        
        Args:
            request_id: ID of request to reject
            approver: Name/ID of person rejecting
            comments: Optional rejection comments
            
        Returns:
            True if successful, False otherwise
        """
        if request_id not in self.pending_requests:
            logger.error(f"Request {request_id} not found in pending requests")
            return False
        
        approval_req = self.pending_requests.pop(request_id)
        approval_req.reject(approver, comments)
        self.completed_requests[request_id] = approval_req
        
        return True
    
    def _notify_human(self, approval_req: ApprovalRequest):
        """
        Notify a human about the approval request
        
        Args:
            approval_req: ApprovalRequest to notify about
        """
        if self.notification_method == "console":
            self._console_notification(approval_req)
        elif self.notification_method == "email":
            # Future: implement email notification
            logger.warning("Email notification not yet implemented, using console")
            self._console_notification(approval_req)
        elif self.notification_method == "slack":
            # Future: implement Slack notification
            logger.warning("Slack notification not yet implemented, using console")
            self._console_notification(approval_req)
        else:
            logger.error(f"Unknown notification method: {self.notification_method}")
    
    def _console_notification(self, approval_req: ApprovalRequest):
        """Print approval request to console"""
        print("\n" + "="*80)
        print("🔔 NEW ACCESS REQUEST REQUIRES APPROVAL")
        print("="*80)
        print(f"Request ID: {approval_req.request_id}")
        print(f"Requester: {approval_req.access_request.requester}")
        print(f"Resource: {approval_req.access_request.resource}")
        print(f"Access Type: {approval_req.access_request.access_type}")
        print(f"Urgency: {approval_req.access_request.urgency}")
        print(f"\nJustification:")
        print(f"  {approval_req.access_request.justification}")
        print(f"\nOriginal Email:")
        print(f"  From: {approval_req.email_data.get('from', 'Unknown')}")
        print(f"  Subject: {approval_req.email_data.get('subject', 'No subject')}")
        print(f"  Date: {approval_req.email_data.get('date', 'Unknown')}")
        print("="*80)
        print("Use agent.approve_request() or agent.reject_request() to respond")
        print("="*80 + "\n")

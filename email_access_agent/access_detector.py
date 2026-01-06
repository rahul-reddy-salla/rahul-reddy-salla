"""
Access Request Detection Module
Uses Langchain to detect and parse access requests from email content
"""

from typing import Dict, Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class AccessRequest(BaseModel):
    """Structured access request"""
    is_access_request: bool = Field(description="Whether this email contains an access request")
    requester: str = Field(description="Name or email of the person requesting access")
    resource: str = Field(description="The resource or system access is requested for")
    access_type: str = Field(description="Type of access requested (e.g., read, write, admin)")
    justification: str = Field(description="Reason or justification for the access request")
    urgency: str = Field(description="Urgency level: low, medium, or high")


class AccessRequestDetector:
    """
    Detects and parses access requests from email content using Langchain
    """
    
    def __init__(self, llm):
        """
        Initialize the access request detector
        
        Args:
            llm: Langchain LLM instance (e.g., ChatOpenAI, ChatAnthropic)
        """
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=AccessRequest)
        
        # Create the detection prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing emails to detect access requests.
            
An access request is any email where someone is asking for:
- Access to a system, application, or resource
- Permission to perform certain actions
- Credentials or accounts
- Role changes or privilege escalations

Analyze the email and extract structured information about the access request.
If this is not an access request, set is_access_request to false.

{format_instructions}"""),
            ("user", """Subject: {subject}
From: {from_address}

Email Body:
{body}

Analyze this email and determine if it contains an access request.""")
        ])
        
        self.chain = self.prompt | self.llm | self.parser
    
    def detect_access_request(self, email_data: Dict) -> Optional[AccessRequest]:
        """
        Detect if an email contains an access request
        
        Args:
            email_data: Dictionary with email information (subject, from, body)
            
        Returns:
            AccessRequest object if request detected, None otherwise
        """
        try:
            result = self.chain.invoke({
                "subject": email_data.get("subject", ""),
                "from_address": email_data.get("from", ""),
                "body": email_data.get("body", ""),
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Convert dict to AccessRequest if needed
            if isinstance(result, dict):
                access_request = AccessRequest(**result)
            else:
                access_request = result
            
            if access_request.is_access_request:
                logger.info(f"Access request detected from {access_request.requester} for {access_request.resource}")
                return access_request
            else:
                logger.debug("No access request detected in email")
                return None
                
        except Exception as e:
            logger.error(f"Error detecting access request: {e}")
            return None
    
    def batch_detect(self, emails: List[Dict]) -> List[tuple[Dict, AccessRequest]]:
        """
        Detect access requests in a batch of emails
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            List of tuples (email_data, access_request) for emails containing requests
        """
        requests = []
        
        for email_data in emails:
            access_request = self.detect_access_request(email_data)
            if access_request:
                requests.append((email_data, access_request))
        
        logger.info(f"Found {len(requests)} access requests in {len(emails)} emails")
        return requests

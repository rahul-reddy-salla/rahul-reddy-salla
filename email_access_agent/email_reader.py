"""
Email Reader Module
Handles reading emails from various sources (IMAP, Gmail API, etc.)
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class EmailReader:
    """
    Email reader that connects to an email server and retrieves messages
    """
    
    def __init__(self, email_address: str, password: str, imap_server: str = "imap.gmail.com"):
        """
        Initialize email reader
        
        Args:
            email_address: Email address to connect to
            password: Password or app-specific password
            imap_server: IMAP server address
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.mail = None
    
    def connect(self) -> bool:
        """
        Connect to the email server
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_address, self.password)
            logger.info(f"Successfully connected to {self.imap_server}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the email server"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
                logger.info("Disconnected from email server")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
    
    def get_unread_emails(self, mailbox: str = "INBOX", limit: int = 10) -> List[Dict]:
        """
        Retrieve unread emails from the specified mailbox
        
        Args:
            mailbox: Mailbox to read from (default: INBOX)
            limit: Maximum number of emails to retrieve
            
        Returns:
            List of email dictionaries with subject, from, body, and date
        """
        if not self.mail:
            logger.error("Not connected to email server")
            return []
        
        try:
            self.mail.select(mailbox)
            
            # Search for unread emails
            status, messages = self.mail.search(None, "UNSEEN")
            
            if status != "OK":
                logger.error("Failed to search for emails")
                return []
            
            email_ids = messages[0].split()
            emails = []
            
            # Process emails in reverse order (newest first)
            for email_id in reversed(email_ids[-limit:]):
                try:
                    email_data = self._fetch_email(email_id)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(emails)} unread emails")
            return emails
            
        except Exception as e:
            logger.error(f"Error retrieving emails: {e}")
            return []
    
    def _fetch_email(self, email_id: bytes) -> Optional[Dict]:
        """
        Fetch and parse a single email
        
        Args:
            email_id: Email ID to fetch
            
        Returns:
            Dictionary with email data or None if failed
        """
        try:
            status, msg_data = self.mail.fetch(email_id, "(RFC822)")
            
            if status != "OK":
                return None
            
            # Parse email content
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Decode subject
            subject = self._decode_header(email_message["Subject"])
            from_addr = self._decode_header(email_message["From"])
            date = email_message["Date"]
            
            # Extract body
            body = self._get_email_body(email_message)
            
            return {
                "id": email_id.decode(),
                "subject": subject,
                "from": from_addr,
                "date": date,
                "body": body
            }
            
        except Exception as e:
            logger.error(f"Error fetching email: {e}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or "utf-8", errors="ignore")
            else:
                decoded_string += part
        
        return decoded_string
    
    def _get_email_body(self, email_message) -> str:
        """Extract email body from message"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
                    except Exception:
                        continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode(errors="ignore")
            except Exception:
                body = ""
        
        return body

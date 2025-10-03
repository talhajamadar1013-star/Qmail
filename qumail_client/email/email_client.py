"""
Email Client for QuMail
Handles secure email sending and receiving
"""

import logging
import smtplib
import imaplib
import email
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EmailClient:
    """Email client for sending and receiving secure emails"""
    
    def __init__(self, config):
        self.config = config
        self.smtp_server = getattr(config, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(config, 'SMTP_PORT', 587)
        self.imap_server = getattr(config, 'IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = getattr(config, 'IMAP_PORT', 993)
        self.system_email = getattr(config, 'SYSTEM_EMAIL', None)
        self.system_password = getattr(config, 'SYSTEM_EMAIL_PASSWORD', None)
        
        # Check if credentials are configured
        if not self.system_email or not self.system_password:
            logger.warning("Email credentials not configured - running in demo mode")
        else:
            logger.info("Email client initialized with SMTP configuration")
        
        logger.info("Email client initialized")
    
    def send_secure_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send secure email with optional attachments"""
        try:
            recipient = email_data.get('recipient')
            subject = email_data.get('subject')
            encrypted_content = email_data.get('encrypted_content')
            attachments = email_data.get('attachments', [])
            
            logger.info(f"Sending secure email to {recipient}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Encrypted content length: {len(encrypted_content) if encrypted_content else 0}")
            if attachments:
                logger.info(f"Attachments: {len(attachments)} file(s)")
            
            # If real email credentials are configured, try to send actual email
            if self.system_email and self.system_password:
                result = self._send_real_email(email_data)
                if result:
                    return {'success': True, 'message': 'Email sent successfully'}
                else:
                    return {'success': False, 'error': 'Failed to send email'}
            else:
                # No email credentials configured
                logger.error("Email credentials not configured")
                return {'success': False, 'error': 'Email credentials not configured'}
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_demo_email(self, email_data: Dict[str, Any]) -> bool:
        """Demo mode email sending - just log the action"""
        logger.info("Demo mode: Email sending simulated")
        logger.info(f"Would send to: {email_data.get('recipient')}")
        logger.info(f"Subject: {email_data.get('subject')}")
        if email_data.get('attachments'):
            logger.info(f"Would include {len(email_data.get('attachments'))} attachment(s)")
        return True
    
    def _send_real_email(self, email_data: Dict[str, Any]) -> bool:
        """Send actual email via SMTP"""
        try:
            msg = MIMEMultipart()
            
            # Use the actual sender if provided, fallback to system email
            sender_email = email_data.get('sender', self.system_email)
            msg['From'] = f"{sender_email} (via QuMail)"
            msg['To'] = email_data.get('recipient')
            msg['Subject'] = email_data.get('subject')
            
            # Create email body with sender information
            encrypted_hash = email_data.get('encrypted_content', '')
            if isinstance(encrypted_hash, bytes):
                encrypted_hash = encrypted_hash.hex()
            
            attachments = email_data.get('attachments', [])
            attachment_info = ""
            if attachments:
                attachment_info = f"\n\nAttachments ({len(attachments)} files):\n" + "\n".join([f"- {os.path.basename(att) if isinstance(att, str) else att.get('filename', 'Unknown')}" for att in attachments])
            
            body = f"""This is a secure email sent via QuMail - Quantum Secure Email Client.

From: {sender_email}
To: {email_data.get('recipient')}

The content has been encrypted using quantum encryption and stored on IPFS.
To view the decrypted content, please log into QuMail with the recipient email address.{attachment_info}

Encrypted Content Hash: {encrypted_hash[:50]}...

QuMail Team"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Handle file attachments
            if attachments:
                logger.info(f"Processing {len(attachments)} attachments")
                for attachment in attachments:
                    try:
                        if isinstance(attachment, str):  # File path
                            if os.path.exists(attachment):
                                with open(attachment, "rb") as f:
                                    part = MIMEBase('application', 'octet-stream')
                                    part.set_payload(f.read())
                                    encoders.encode_base64(part)
                                    part.add_header(
                                        'Content-Disposition',
                                        f'attachment; filename= {os.path.basename(attachment)}'
                                    )
                                    msg.attach(part)
                                    logger.info(f"Attached file: {os.path.basename(attachment)}")
                        elif isinstance(attachment, dict):  # File data dict
                            filename = attachment.get('filename', 'attachment')
                            file_data = attachment.get('data', b'')
                            if file_data:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(file_data)
                                encoders.encode_base64(part)
                                part.add_header(
                                    'Content-Disposition',
                                    f'attachment; filename= {filename}'
                                )
                                msg.attach(part)
                                logger.info(f"Attached file: {filename}")
                    except Exception as e:
                        logger.warning(f"Failed to attach file: {e}")
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.system_email, self.system_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.system_email, email_data.get('recipient'), text)
            server.quit()
            
            logger.info(f"Email sent successfully from {sender_email} to {email_data.get('recipient')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send real email: {e}")
            return False
    
    def get_inbox_emails(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get inbox emails"""
        try:
            # If real email credentials are configured, fetch real emails
            if self.system_email and self.system_password:
                return self._get_real_emails(limit)
            else:
                # Demo data
                return [
                    {
                        'id': 1,
                        'sender': 'demo@qumail.com',
                        'subject': 'Welcome to QuMail - Quantum Secure Email',
                        'timestamp': '2024-01-01 12:00:00',
                        'encrypted': True,
                        'read': False
                    },
                    {
                        'id': 2,
                        'sender': 'security@qumail.com',
                        'subject': 'Your Quantum Keys are Ready',
                        'timestamp': '2024-01-01 10:30:00',
                        'encrypted': True,
                        'read': True
                    },
                    {
                        'id': 3,
                        'sender': 'support@qumail.com',
                        'subject': 'QuMail Setup Complete',
                        'timestamp': '2024-01-01 09:15:00',
                        'encrypted': True,
                        'read': True
                    }
                ]
                
        except Exception as e:
            logger.error(f"Failed to get inbox: {e}")
            return []
    
    def _get_real_emails(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get real emails from IMAP server"""
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.system_email, self.system_password)
            mail.select('inbox')
            
            # Search for emails
            result, messages = mail.search(None, 'ALL')
            
            if result != 'OK':
                return []
            
            emails = []
            message_ids = messages[0].split()
            
            # Get latest emails (limited by limit parameter)
            for msg_id in message_ids[-limit:]:
                try:
                    result, msg_data = mail.fetch(msg_id, '(RFC822)')
                    
                    if result != 'OK':
                        continue
                    
                    # Parse email
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Extract email info
                    sender = email_message['From']
                    subject = email_message['Subject']
                    date = email_message['Date']
                    
                    emails.append({
                        'id': int(msg_id),
                        'sender': sender,
                        'subject': subject or '(No Subject)',
                        'timestamp': date or 'Unknown',
                        'encrypted': '[QuMail]' in (subject or ''),
                        'read': False  # Simplified - in real implementation, track read status
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to parse email {msg_id}: {e}")
                    continue
            
            mail.close()
            mail.logout()
            
            # Reverse to show newest first
            emails.reverse()
            return emails
            
        except Exception as e:
            logger.error(f"Failed to fetch real emails: {e}")
            return []
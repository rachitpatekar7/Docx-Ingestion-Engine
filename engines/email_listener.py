"""
Email Listener Module

This module handles Gmail IMAP connection and email monitoring.
It provides functionality to:
- Connect to Gmail using IMAP protocol
- Search for emails based on criteria (date, read status, etc.)
- Filter emails for insurance-related content
- Download and save email attachments
- Extract email metadata and content

Key Features:
- Secure IMAP connection with app passwords
- Insurance keyword filtering
- Attachment handling for PDF and image files
- Email content extraction with proper encoding
"""

# Standard library imports for email operations
import os
import time
import imaplib  # IMAP client for Gmail connection
import email    # Email parsing and handling
from email.header import decode_header  # Decode email headers properly
from datetime import datetime, timedelta  # Date handling for email filtering

# Import our Google Drive uploader for saving processed emails
from drive_uploader import save_email_and_attachments

class EmailListener:
    """
    Gmail IMAP client for monitoring and processing emails.
    
    This class provides methods to:
    - Connect to Gmail via IMAP
    - Search for emails with specific criteria
    - Filter emails based on insurance-related keywords
    - Download and process email attachments
    - Track processed emails to avoid duplicates
    """
    
    def __init__(self, email_address, app_password):
        """
        Initialize the email listener with Gmail credentials.
        
        Args:
            email_address (str): Gmail address for IMAP connection
            app_password (str): Gmail app password (not regular password)
        """
        self.email_address = email_address
        self.app_password = app_password
        self.imap = None  # Will hold the IMAP connection object
        self.seen_uids = set()  # Track processed email UIDs to avoid duplicates

    def connect(self):
        """
        Establish secure IMAP connection to Gmail server.
        This must be called before any email operations.
        """
        print("[CONNECT] Connecting to Gmail via IMAP...")
        # Create secure IMAP connection to Gmail
        self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
        # Login with app password (more secure than regular password)
        self.imap.login(self.email_address, self.app_password)
        # Select the inbox folder for email operations
        self.imap.select("inbox")
        print("[SUCCESS] Connected.")

    def is_insurance_email(self, msg):
        """
        Check if an email is related to insurance based on subject keywords.
        
        Args:
            msg: Email message object
            
        Returns:
            bool: True if email appears to be insurance-related, False otherwise
        """
        subject = msg["Subject"]
        if subject:
            # Decode the subject header properly (handles encoding)
            decoded_subject, encoding = decode_header(subject)[0]
            if isinstance(decoded_subject, bytes):
                decoded_subject = decoded_subject.decode(encoding or "utf-8", errors="ignore")
            
            # List of keywords that indicate insurance-related emails
            keywords = ["insurance", "policy", "premium", "claim", "renewal"]
            # Check if any insurance keywords appear in the subject (case-insensitive)
            return any(keyword in decoded_subject.lower() for keyword in keywords)
        return False

    def get_decoded(self, header_val):
        """
        Properly decode email header values that may be encoded.
        
        Args:
            header_val (str): Raw header value from email
            
        Returns:
            str: Decoded header string
        """
        decoded_parts = decode_header(header_val)
        decoded_string = ''
        
        # Process each part of the header (may have multiple encoded sections)
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                # Decode bytes using specified encoding or UTF-8 as fallback
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                # Already a string, just append
                decoded_string += part
        return decoded_string

    def extract_email_data(self, msg):
        """
        Extract key information from an email message.
        
        Args:
            msg: Email message object
            
        Returns:
            tuple: (to, cc, subject, body) extracted from the email
        """
        # Extract basic header information
        to = msg.get("To", "")
        cc = msg.get("Cc", "")
        subject = self.get_decoded(msg.get("Subject", ""))
        body = ""

        # Extract email body content (handles both plain text and HTML)
        if msg.is_multipart():
            # Email has multiple parts (text, HTML, attachments)
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Look for text content that's not an attachment
                if "attachment" not in content_disposition and content_type in ("text/plain", "text/html"):
                    charset = part.get_content_charset() or "utf-8"
                    body = part.get_payload(decode=True).decode(charset, errors="ignore")
                    break  # Use first text part found
        else:
            # Simple email with single content type
            charset = msg.get_content_charset() or "utf-8"
            body = msg.get_payload(decode=True).decode(charset, errors="ignore")

        return to, cc, subject, body.strip()

    def save_attachments(self, msg):
        """
        Download and save all attachments from an email message.
        
        Args:
            msg: Email message object
            
        Returns:
            str or None: Path to attachment directory if attachments found, None otherwise
        """
        # Create unique directory for this email's attachments
        attachment_dir = os.path.join("attachments", f"email_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        os.makedirs(attachment_dir, exist_ok=True)
        attachment_found = False

        # Walk through all parts of the email message
        for part in msg.walk():
            # Skip multipart containers
            if part.get_content_maintype() == "multipart":
                continue
            # Skip parts that aren't attachments
            if part.get("Content-Disposition") is None:
                continue

            # Extract attachment filename
            filename = part.get_filename()
            if filename:
                # Properly decode filename (may be encoded)
                decoded_name, encoding = decode_header(filename)[0]
                if isinstance(decoded_name, bytes):
                    filename = decoded_name.decode(encoding or "utf-8", errors="ignore")

                # Save attachment to file
                filepath = os.path.join(attachment_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))

                print(f"[ATTACH] Saved attachment: {filename}")
                attachment_found = True

        # Return directory path if attachments were found, None otherwise
        return attachment_dir if attachment_found else None

    def check_inbox(self):
        date_since = (datetime.now() - timedelta(days=3)).strftime("%d-%b-%Y")
        status, messages = self.imap.uid("search", None, f'(UNSEEN SINCE {date_since})')

        if status != "OK":
            print("[WARNING] Failed to fetch messages.")
            return

        for uid in messages[0].split():
            if uid in self.seen_uids:
                continue

            self.seen_uids.add(uid)
            _, msg_data = self.imap.uid("fetch", uid, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            if not self.is_insurance_email(msg):
                continue  # Skip non-insurance emails

            to, cc, subject, body = self.extract_email_data(msg)
            from_ = msg.get("From")
            date_ = msg.get("Date")

            print("\n[EMAIL] Insurance Email received:")
            print(f"From: {from_}")
            print(f"To: {to}")
            print(f"Cc: {cc}")
            print(f"Subject: {subject}")
            print(f"Date: {date_}")
            print("-" * 40)

            attachments_dir = self.save_attachments(msg)
            save_email_and_attachments(to, cc, subject, body, attachments_dir or "")

    def listen(self, interval=60):
        try:
            print("Listening for insurance emails every", interval, "seconds...")
            while True:
                self.check_inbox()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("[STOP] Stopped listening.")
            self.imap.logout()

#!/usr/bin/env python3
"""
Integrated Email-to-Invoice Processing System

This is the core processing engine that combines multiple components:
1. Email listening and connection to Gmail via IMAP
2. PDF/image extraction from email attachments 
3. Invoice data processing using OCR and AI
4. Google Drive storage and organization

The system automatically:
- Connects to Gmail and monitors for insurance-related emails
- Downloads and processes PDF/image attachments
- Extracts structured data from invoices
- Uploads results to Google Drive with organized folder structure
- Provides links back to the uploaded content
"""

# Standard library imports for file operations, time handling, etc.
import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path
import email

# Add the paths for importing our custom modules
# This allows us to import from subdirectories
sys.path.append(os.path.join(os.path.dirname(__file__), 'engines'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'invoice_reader'))

# Import our custom modules for different functionalities
from engines.email_listener import EmailListener  # Handles Gmail IMAP connection
from engines.drive_uploader import create_drive_folder, upload_file, authenticate_drive  # Google Drive operations
from invoice_reader.backend import get_pdf_text_with_ocr, process_image, extracted_data, create_docs  # Invoice processing
from invoice_reader.logging_config import logger  # Logging configuration

class IntegratedEmailInvoiceProcessor:
    """
    Main processor class that orchestrates the entire email-to-invoice pipeline.
    
    This class handles:
    - Email connection and monitoring
    - Attachment processing
    - Invoice data extraction
    - Google Drive upload and organization
    - Error handling and logging
    """
    
    def __init__(self, email_address, app_password):
        """
        Initialize the processor with email credentials.
        
        Args:
            email_address (str): Gmail address for accessing emails
            app_password (str): Gmail app password (not regular password)
        """
        self.email_address = email_address
        self.app_password = app_password
        # Create email listener instance for Gmail connection
        self.email_listener = EmailListener(email_address, app_password)
        # List to store all processed invoice results
        self.processed_invoices = []
        
    def connect(self):
        """
        Connect to the Gmail server using IMAP protocol.
        This must be called before any email operations.
        """
        logger.info("Connecting to email server...")
        self.email_listener.connect()
        logger.info("Successfully connected to email server")
    
    def process_invoice_attachments(self, attachments_dir):
        """
        Process PDF and image attachments to extract invoice data.
        
        Args:
            attachments_dir (str): Path to directory containing downloaded attachments
            
        Returns:
            pandas.DataFrame or None: Extracted invoice data or None if processing failed
        """
        # Validate that attachments directory exists
        if not attachments_dir or not os.path.exists(attachments_dir):
            logger.warning("No attachments directory found")
            return None
        
        # Find all PDF and image files in the attachments directory
        attachment_files = []
        for file in os.listdir(attachments_dir):
            file_path = os.path.join(attachments_dir, file)
            # Check for supported file extensions
            if file.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                attachment_files.append(file_path)
        
        # Check if we found any processable files
        if not attachment_files:
            logger.warning("No PDF or image files found in attachments")
            return None
        
        logger.info(f"Found {len(attachment_files)} invoice files to process")
        
        # Create mock file objects that are compatible with the invoice reader
        mock_files = []
        for file_path in attachment_files:
            mock_file = self.create_mock_file(file_path)
            if mock_file:
                mock_files.append(mock_file)
        
        # Ensure we have valid files to process
        if not mock_files:
            logger.warning("No valid files could be processed")
            return None
        
        # Process files using the invoice reader backend
        logger.info("Processing invoice files...")
        df = create_docs(mock_files)
        
        # Return results if successful
        if not df.empty:
            logger.info(f"Successfully extracted data from {len(df)} invoice items")
            return df
        else:
            logger.warning("No data could be extracted from invoice files")
            return None
    
    def create_mock_file(self, file_path):
        """
        Create a mock file object that mimics uploaded files for the invoice reader.
        
        The invoice reader expects file objects with specific attributes,
        so we create a mock object that provides the necessary interface.
        
        Args:
            file_path (str): Path to the actual file on disk
            
        Returns:
            MockFile object or None: Mock file object or None if creation failed
        """
        try:
            class MockFile:
                """
                Mock file object that mimics the interface expected by invoice reader.
                """
                def __init__(self, filepath):
                    # Store file information
                    self.name = os.path.basename(filepath)
                    self.file_path = filepath
                    
                    # Determine MIME type based on file extension
                    if filepath.lower().endswith('.pdf'):
                        self.type = 'application/pdf'
                    elif filepath.lower().endswith(('.jpg', '.jpeg')):
                        self.type = 'image/jpeg'
                    elif filepath.lower().endswith('.png'):
                        self.type = 'image/png'
                    else:
                        self.type = 'application/octet-stream'
                        
                def read(self):
                    """
                    Read the file contents as bytes.
                    This method is expected by the invoice reader.
                    """
                    with open(self.file_path, 'rb') as f:
                        return f.read()
            
            return MockFile(file_path)
        except Exception as e:
            logger.error(f"Error creating mock file for {file_path}: {e}")
            return None
    
    def save_to_google_drive(self, invoice_data, email_metadata, attachments_dir):
        """Save invoice data, CSV, and files to Google Drive"""
        try:
            # Create Google Drive service
            service = authenticate_drive()
            
            # Create a unique folder name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"Invoice_Processing_{timestamp}"
            
            logger.info(f"Creating Google Drive folder: {folder_name}")
            folder_id = create_drive_folder(service, folder_name)
            
            if not folder_id:
                logger.error("Failed to create Google Drive folder")
                return None
            
            drive_link = f"https://drive.google.com/drive/folders/{folder_id}"
            logger.info(f"Created folder: {drive_link}")
            
            uploaded_files = []
            
            # 1. Save invoice data as CSV (temporarily for upload, then delete)
            if invoice_data is not None and not invoice_data.empty:
                csv_filename = f"invoice_data_{timestamp}.csv"
                csv_path = os.path.join(attachments_dir, csv_filename)
                invoice_data.to_csv(csv_path, index=False)
                
                csv_file_id = upload_file(service, csv_path, csv_filename, folder_id)
                if csv_file_id:
                    uploaded_files.append({"name": csv_filename, "id": csv_file_id, "type": "CSV"})
                    logger.info(f"Uploaded CSV: {csv_filename}")
                    # Delete local CSV file after successful upload
                    try:
                        os.remove(csv_path)
                        logger.info(f"Deleted local CSV file: {csv_filename}")
                    except Exception as e:
                        logger.warning(f"Could not delete local CSV: {e}")
            
            # 2. Save email metadata as JSON (temporarily for upload, then delete)
            metadata_filename = f"email_metadata_{timestamp}.json"
            metadata_path = os.path.join(attachments_dir, metadata_filename)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(email_metadata, f, indent=2, ensure_ascii=False)
            
            metadata_file_id = upload_file(service, metadata_path, metadata_filename, folder_id)
            if metadata_file_id:
                uploaded_files.append({"name": metadata_filename, "id": metadata_file_id, "type": "Metadata"})
                logger.info(f"Uploaded metadata: {metadata_filename}")
                # Delete local metadata file after successful upload
                try:
                    os.remove(metadata_path)
                    logger.info(f"Deleted local metadata file: {metadata_filename}")
                except Exception as e:
                    logger.warning(f"Could not delete local metadata: {e}")
            
            # 3. Upload original PDF/image attachments and delete after upload
            if attachments_dir and os.path.exists(attachments_dir):
                for file in os.listdir(attachments_dir):
                    file_path = os.path.join(attachments_dir, file)
                    if os.path.isfile(file_path) and file.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                        file_id = upload_file(service, file_path, file, folder_id)
                        if file_id:
                            uploaded_files.append({"name": file, "id": file_id, "type": "Original"})
                            logger.info(f"Uploaded original file: {file}")
                            # Delete local file after successful upload
                            try:
                                os.remove(file_path)
                                logger.info(f"Deleted local file: {file}")
                            except Exception as e:
                                logger.warning(f"Could not delete local file {file}: {e}")
                
                # Try to remove the empty attachments directory
                try:
                    if not os.listdir(attachments_dir):  # Only if empty
                        os.rmdir(attachments_dir)
                        logger.info(f"Deleted empty attachments directory: {attachments_dir}")
                except Exception as e:
                    logger.warning(f"Could not delete attachments directory: {e}")
            
            return {
                "drive_link": drive_link,
                "folder_id": folder_id,
                "uploaded_files": uploaded_files
            }
            
        except Exception as e:
            logger.error(f"Error saving to Google Drive: {e}")
            logger.info("Files will be kept locally as fallback")
            return None
    
    def process_single_email(self, uid, msg):
        """Process a single email with invoice attachments"""
        try:
            # Extract email data
            to, cc, subject, body = self.email_listener.extract_email_data(msg)
            from_ = msg.get("From")
            date_ = msg.get("Date")
            
            logger.info(f"Processing email: {subject}")
            
            # Save attachments
            attachments_dir = self.email_listener.save_attachments(msg)
            
            if not attachments_dir:
                logger.warning("No attachments found in email")
                return None
            
            # Create email metadata
            email_metadata = {
                "from": from_,
                "to": to,
                "cc": cc,
                "subject": subject,
                "date": date_,
                "body": body,
                "processed_at": datetime.now().isoformat()
            }
            
            # Process invoice attachments
            invoice_data = self.process_invoice_attachments(attachments_dir)
            
            # Save everything to Google Drive
            drive_result = self.save_to_google_drive(invoice_data, email_metadata, attachments_dir)
            
            if drive_result:
                result = {
                    "email_metadata": email_metadata,
                    "invoice_data": invoice_data.to_dict('records') if invoice_data is not None else [],
                    "drive_link": drive_result["drive_link"],
                    "uploaded_files": drive_result["uploaded_files"],
                    "processed_at": datetime.now().isoformat()
                }
                
                self.processed_invoices.append(result)
                
                logger.info(f"Successfully processed email and saved to: {drive_result['drive_link']}")
                return result
            else:
                logger.error("Failed to save to Google Drive")
                return None
                
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return None
    
    def reset_seen_emails(self):
        """Reset the seen emails cache to reprocess emails"""
        self.email_listener.seen_uids.clear()
        logger.info("Reset seen emails cache")
    
    def check_and_process_emails(self, force_reprocess=False):
        """Check for new emails and process them"""
        try:
            if force_reprocess:
                self.reset_seen_emails()
                
            date_since = (datetime.now() - timedelta(days=3)).strftime("%d-%b-%Y")
            # Only get UNREAD emails from the last 3 days, unless forcing reprocess
            if force_reprocess:
                status, messages = self.email_listener.imap.uid("search", None, f'(SINCE {date_since})')
                logger.info("Force reprocess: checking all emails from last 3 days")
            else:
                status, messages = self.email_listener.imap.uid("search", None, f'(UNSEEN SINCE {date_since})')
                logger.info("Normal check: only looking for unread emails")

            if status != "OK":
                logger.warning("Failed to fetch messages")
                return []

            email_count = len(messages[0].split()) if messages[0] else 0
            logger.info(f"Found {email_count} emails to check")
            processed_results = []
            
            for uid in messages[0].split():
                if uid in self.email_listener.seen_uids:
                    logger.debug(f"Skipping already processed email UID: {uid}")
                    continue

                self.email_listener.seen_uids.add(uid)
                _, msg_data = self.email_listener.imap.uid("fetch", uid, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                if not self.email_listener.is_insurance_email(msg):
                    logger.debug(f"Skipping non-insurance email: {msg.get('Subject', 'No Subject')}")
                    continue  # Skip non-insurance emails

                logger.info("Found insurance email, processing...")
                result = self.process_single_email(uid, msg)
                
                if result:
                    processed_results.append(result)
            
            logger.info(f"Processed {len(processed_results)} insurance emails")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error checking emails: {e}")
            return []
    
    def run_continuous(self, interval=60):
        """Run continuous email monitoring and processing"""
        try:
            self.connect()
            logger.info(f"Starting continuous email monitoring (checking every {interval} seconds)...")
            
            while True:
                logger.info("Checking for new emails...")
                results = self.check_and_process_emails()
                
                if results:
                    logger.info(f"Processed {len(results)} emails this cycle")
                    for result in results:
                        logger.info(f"Invoice data extracted: {len(result['invoice_data'])} items")
                        logger.info(f"Google Drive: {result['drive_link']}")
                else:
                    logger.info("No new insurance emails found")
                
                logger.info(f"Waiting {interval} seconds before next check...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Stopping email processor...")
            if self.email_listener.imap:
                self.email_listener.imap.logout()
        except Exception as e:
            logger.error(f"Error in continuous processing: {e}")

if __name__ == "__main__":
    # Configuration
    EMAIL = "canspirittest@gmail.com"
    PASSWORD = "ylyh hkml dgxn vdpi"
    
    logger.info("Starting Integrated Email-to-Invoice Processor")
    
    processor = IntegratedEmailInvoiceProcessor(EMAIL, PASSWORD)
    processor.run_continuous(interval=60)

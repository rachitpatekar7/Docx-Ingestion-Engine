#!/usr/bin/env python3
"""
Streamlit Dashboard for Integrated Email-to-Invoice Processing
Shows real-time email processing, invoice extraction, and Google Drive uploads

This is the main web interface that allows users to:
1. Connect to their Gmail account
2. Check for insurance-related emails with attachments
3. Process PDF/image invoices using OCR and AI
4. Upload results to Google Drive
5. View processing logs and results in real-time
"""

# Import required libraries for the web interface
import streamlit as st  # Web framework for creating the dashboard
import pandas as pd     # Data manipulation for displaying results in tables
import json            # For handling JSON data structures
import time            # For timing operations and delays
import threading       # For background processes (if needed)
from datetime import datetime  # For timestamp handling
import sys             # For system path management
import os              # For file system operations

# Add current directory to Python path so we can import our custom modules
sys.path.append(os.path.dirname(__file__))
from integrated_email_invoice_processor import IntegratedEmailInvoiceProcessor

# Configure Streamlit page settings - must be called first
st.set_page_config(
    page_title="Email-to-Invoice Processor",  # Browser tab title
    layout="wide",                            # Use full width of browser
    initial_sidebar_state="expanded"          # Start with sidebar open
)

# Custom CSS styling to make the interface look professional
st.markdown("""
<style>
    /* Main header styling */
    .main-header { 
        font-size: 2.5rem; 
        color: #1f77b4; 
        text-align: center; 
        margin-bottom: 2rem; 
    }
    
    /* Metric card styling for statistics display */
    .metric-card { 
        background: #f0f2f6; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        margin: 0.5rem 0; 
    }
    
    /* Success message box styling */
    .success-box { 
        background: #d4edda; 
        border: 1px solid #c3e6cb; 
        color: #155724; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        margin: 1rem 0; 
    }
    
    /* Information message box styling */
    .info-box { 
        background: #d1ecf1; 
        border: 1px solid #bee5eb; 
        color: #0c5460; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        margin: 1rem 0; 
    }
    
    /* Google Drive link styling */
    .drive-link { 
        background: #fff3cd; 
        border: 1px solid #ffeaa7; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        margin: 1rem 0; 
        text-align: center; 
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """
    Initialize session state variables for the Streamlit application.
    Session state allows data to persist between page refreshes.
    """
    # Email processor instance - handles connection to Gmail and processing
    if 'processor' not in st.session_state:
        st.session_state.processor = None
    
    # Flag to track if processing is currently active
    if 'processing_active' not in st.session_state:
        st.session_state.processing_active = False
    
    # List to store all processed email results for display
    if 'processed_emails' not in st.session_state:
        st.session_state.processed_emails = []
    
    # Timestamp of last email check for status display
    if 'last_check' not in st.session_state:
        st.session_state.last_check = None
    
    # List to store processing logs for user feedback
    if 'processing_logs' not in st.session_state:
        st.session_state.processing_logs = []

def add_log(message):
    """
    Add a timestamped log message to the processing logs.
    
    Args:
        message (str): The log message to add
    """
    # Create timestamp in HH:MM:SS format
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    # Add to logs list
    st.session_state.processing_logs.append(log_entry)
    
    # Keep only the most recent 50 logs to prevent memory issues
    if len(st.session_state.processing_logs) > 50:
        st.session_state.processing_logs = st.session_state.processing_logs[-50:]

def create_processor(email, password):
    """
    Create and connect the email processor instance.
    
    Args:
        email (str): Gmail address
        password (str): Gmail app password (not regular password)
        
    Returns:
        IntegratedEmailInvoiceProcessor or None: Connected processor or None if failed
    """
    try:
        # Create processor instance with credentials
        processor = IntegratedEmailInvoiceProcessor(email, password)
        # Attempt to connect to Gmail IMAP server
        processor.connect()
        return processor
    except Exception as e:
        # Display error message to user if connection fails
        st.error(f"Failed to connect: {str(e)}")
        return None

def check_emails_once(processor):
    """
    Check for emails once and return results.
    
    Args:
        processor: The email processor instance
        
    Returns:
        list: List of processed email results
    """
    try:
        # Use the processor to check and process emails
        results = processor.check_and_process_emails()
        # Update last check timestamp
        st.session_state.last_check = datetime.now()
        return results
    except Exception as e:
        # Display error if email checking fails
        st.error(f"Error checking emails: {str(e)}")
        return []

def display_google_drive_button(email_result):
    """
    Display a clickable Google Drive button with email information.
    
    Args:
        email_result (dict): Dictionary containing email processing results
    """
    # Extract email metadata for button display
    metadata = email_result.get('email_metadata', {})
    subject = metadata.get('subject', 'Unknown Subject')
    sender = metadata.get('from', 'Unknown Sender')
    drive_link = email_result.get('drive_link')
    
    # Truncate long text for better button display
    display_subject = subject[:50] + "..." if len(subject) > 50 else subject
    display_sender = sender.split('<')[0].strip() if '<' in sender else sender
    display_sender = display_sender[:30] + "..." if len(display_sender) > 30 else display_sender
    
    # Create button text with subject and sender info
    button_text = f"📧 {display_subject}\n👤 From: {display_sender}"
    
    if drive_link:
        # Create clickable button that opens Google Drive folder
        if st.button(button_text, key=f"drive_{email_result.get('processed_at', '')}", use_container_width=True):
            st.balloons()  # Fun animation when clicked
            st.success(f"🚀 Opening Google Drive folder...")
        
        # Also provide a direct link for backup access
        st.markdown(f"""
        <div style="text-align: center; margin: 5px 0;">
            <a href="{drive_link}" target="_blank" style="
                background: linear-gradient(45deg, #4285f4, #34a853);
                color: white;
                padding: 8px 16px;
                text-decoration: none;
                border-radius: 5px;
                font-size: 14px;
                display: inline-block;
            ">
                🔗 Open in Google Drive
            </a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error(f"❌ Google Drive upload failed for: {display_subject}")

def display_invoice_data(invoice_data):
    """
    Display invoice data in a formatted table with download option.
    
    Args:
        invoice_data: Pandas DataFrame or list containing invoice data
    """
    # Check if we have any data to display
    if invoice_data and len(invoice_data) > 0:
        # Convert to DataFrame if it's not already
        df = pd.DataFrame(invoice_data)
        # Display as interactive table that fills container width
        st.dataframe(df, use_container_width=True)
        
        # Provide CSV download functionality for the user
        csv = df.to_csv(index=False)
        # Create unique key based on timestamp and data hash to avoid duplicate IDs
        unique_key = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(df.values.tobytes())) % 10000}"
        st.download_button(
            label="📥 Download Invoice Data as CSV",
            data=csv,
            file_name=f"invoice_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key=unique_key
        )
    else:
        # Show message when no data is available
        st.info("No invoice data extracted")

def display_email_summary(email_result):
    """
    Display a summary of the processed email in a two-column layout.
    
    Args:
        email_result (dict): Dictionary containing email processing results
    """
    # Extract email metadata from the result
    metadata = email_result.get('email_metadata', {})
    
    # Create two columns for organized display
    col1, col2 = st.columns([1, 1])
    
    # Left column: Email details
    with col1:
        st.write("**📧 Email Details:**")
        st.write(f"**From:** {metadata.get('from', 'N/A')}")
        st.write(f"**Subject:** {metadata.get('subject', 'N/A')}")
        st.write(f"**Date:** {metadata.get('date', 'N/A')}")
        st.write(f"**Processed:** {email_result.get('processed_at', 'N/A')}")
    
    # Right column: Processing results summary
    with col2:
        st.write("**📊 Processing Results:**")
        invoice_data = email_result.get('invoice_data', [])
        uploaded_files = email_result.get('uploaded_files', [])
        
        st.write(f"**Invoice Items:** {len(invoice_data) if invoice_data else 0}")
        st.write(f"**Uploaded Files:** {len(uploaded_files) if uploaded_files else 0}")
        
        # Display uploaded files
        for file_info in uploaded_files:
            if isinstance(file_info, dict):
                st.write(f"• {file_info.get('name', 'Unknown')} ({file_info.get('type', 'Unknown')})")
            else:
                st.write(f"• {file_info}")

def main():
    """
    Main function that creates the Streamlit web interface.
    This function handles the layout, user interactions, and displays results.
    """
    # Initialize session state variables if not already done
    init_session_state()
    
    # Create the main header with emoji and styling
    st.markdown('<h1 class="main-header">🚀 Email-to-Invoice Processor</h1>', unsafe_allow_html=True)
    # Add description of what the application does
    st.markdown("**Automated pipeline:** Email Reader → PDF Extraction → Invoice Processing → Google Drive Storage")
    
    
    # Create sidebar for configuration and controls
    with st.sidebar:
        # Configuration section header
        st.header("⚙️ Configuration")
        
        # Email credentials input fields
        email = st.text_input("📧 Gmail Address", value="canspirittest@gmail.com")
        password = st.text_input("🔑 App Password", value="ylyh hkml dgxn vdpi", type="password")
        
        # Important note about using app passwords instead of regular passwords
        st.info("💡 Use Gmail App Password, not regular password")
        
        # Display connection status to user
        if st.session_state.processor:
            st.success("✅ Connected to email server")
        else:
            st.warning("⚠️ Not connected")
        
        # Control buttons section
        st.header("🎛️ Controls")
        
        # Connect button - creates processor and connects to Gmail
        if st.button("🔌 Connect to Email", disabled=st.session_state.processing_active):
            if email and password:
                add_log("🔌 Attempting to connect to email server...")
                with st.spinner("Connecting to email server..."):
                    st.session_state.processor = create_processor(email, password)
                if st.session_state.processor:
                    add_log("✅ Successfully connected to email server")
                    st.success("Connected successfully!")
                    st.rerun()
                else:
                    add_log("❌ Failed to connect to email server")
        
        if st.button("🔍 Check Emails Once", disabled=not st.session_state.processor):
            if st.session_state.processor:
                add_log("🔍 Starting email check...")
                with st.spinner("Checking for new emails..."):
                    try:
                        # Check for unread emails (not force reprocess by default)
                        add_log("📬 Looking for unread insurance emails...")
                        results = st.session_state.processor.check_and_process_emails(force_reprocess=False)
                        
                        # Display processing status
                        if results:
                            add_log(f"✅ Found {len(results)} new insurance emails")
                            st.session_state.processed_emails.extend(results)
                            
                            # Show what was processed in logs only
                            for result in results:
                                email_meta = result.get('email_metadata', {})
                                subject = email_meta.get('subject', 'Unknown Subject')
                                add_log(f"📧 Processed: {subject}")
                                if result.get('drive_link'):
                                    add_log(f"☁️ Uploaded to Google Drive: {subject}")
                                else:
                                    add_log(f"💾 Saved locally (Google Drive failed): {subject}")
                        else:
                            add_log("📭 No new unread insurance emails found")
                            
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        add_log(error_msg)
                        import traceback
                        add_log(f"Error details: {traceback.format_exc()}")
                st.rerun()
        
        # Add a separate button for force reprocess (check all emails from last 3 days)
        if st.button("🔄 Force Check All Emails (Last 3 Days)", disabled=not st.session_state.processor):
            if st.session_state.processor:
                add_log("🔄 Starting force check of all emails from last 3 days...")
                with st.spinner("Checking all emails from last 3 days..."):
                    try:
                        # Force reprocess to get all emails from last 3 days
                        add_log("📬 Searching all emails from last 3 days...")
                        results = st.session_state.processor.check_and_process_emails(force_reprocess=True)
                        
                        if results:
                            add_log(f"✅ Found {len(results)} insurance emails from last 3 days")
                            st.session_state.processed_emails.extend(results)
                            
                            # Show what was processed in logs only
                            for result in results:
                                email_meta = result.get('email_metadata', {})
                                subject = email_meta.get('subject', 'Unknown Subject')
                                add_log(f"📧 Processed: {subject}")
                                if result.get('drive_link'):
                                    add_log(f"☁️ Uploaded to Google Drive: {subject}")
                                else:
                                    add_log(f"💾 Saved locally (Google Drive failed): {subject}")
                        else:
                            add_log("📭 No insurance emails found in last 3 days")
                            
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        add_log(error_msg)
                        import traceback
                        add_log(f"Error details: {traceback.format_exc()}")
                st.rerun()
        
        # Add reset button
        if st.button("🔄 Reset Email Cache", disabled=not st.session_state.processor):
            if st.session_state.processor:
                add_log("🔄 Resetting email cache...")
                st.session_state.processor.reset_seen_emails()
                st.session_state.processed_emails = []  # Clear dashboard cache too
                add_log("✅ Email cache reset successfully")
                st.success("🔄 Email cache reset!")
                st.rerun()
    
    # Main content area - split into two columns
    main_col1, main_col2 = st.columns([2, 1])
    
    with main_col1:
        # Display processing logs
        st.header("� Processing Logs")
        if st.session_state.processing_logs:
            # Create a container for scrollable logs
            log_container = st.container()
            with log_container:
                # Show logs in reverse order (newest first)
                for log in reversed(st.session_state.processing_logs[-15:]):  # Show last 15 logs
                    st.text(log)
            
            if st.button("�️ Clear Logs", key="clear_logs_main"):
                st.session_state.processing_logs = []
                st.rerun()
        else:
            st.info("🔄 Processing logs will appear here...")
        
        # Display processed emails with Google Drive buttons
        if st.session_state.processed_emails:
            st.header("📋 Processed Emails & Google Drive Links")
            
            # Show emails in reverse order (newest first)
            for i, email_result in enumerate(reversed(st.session_state.processed_emails)):
                with st.expander(f"📧 Email {len(st.session_state.processed_emails) - i}: {email_result['email_metadata']['subject'][:60]}{'...' if len(email_result['email_metadata']['subject']) > 60 else ''}", expanded=False):
                    
                    # Google Drive button
                    display_google_drive_button(email_result)
                    
                    # Email summary
                    display_email_summary(email_result)
                    
                    # Invoice data
                    if email_result.get('invoice_data'):
                        st.subheader("📊 Extracted Invoice Data")
                        display_invoice_data(email_result['invoice_data'])
        else:
            st.header("🎯 Quick Start")
            st.info("👋 Connect to email and check for emails to get started!")
            
            # Show instructions
            st.markdown("""
            ## 🎯 How it works:
            
            1. **📧 Connect** to your Gmail account using app password
            2. **🔍 Check emails** for insurance-related messages with PDF attachments
            3. **📄 Extract data** from PDF invoices using OCR and AI
            4. **📊 Display results** in a structured table format
            5. **☁️ Upload to Google Drive** with CSV, metadata, and original files
            6. **🔗 Get shareable link** to the Google Drive folder
            
            ### 📋 What gets uploaded to Google Drive:
            - **📊 CSV file** with extracted invoice data
            - **📝 JSON metadata** with email details
            - **📎 Original PDF/image** attachments
            """)
    
    with main_col2:
        # Statistics and Quick Actions
        st.header("📊 Quick Stats")
        
        # Metrics in column 2
        st.metric(
            label="📊 Total Processed",
            value=len(st.session_state.processed_emails)
        )
        
        st.metric(
            label="🕒 Last Check",
            value=st.session_state.last_check.strftime("%H:%M:%S") if st.session_state.last_check else "Never"
        )
        
        st.metric(
            label="🔗 Status",
            value="Connected" if st.session_state.processor else "Disconnected"
        )
        
        # Recent activity
        if st.session_state.processed_emails:
            st.subheader("🎯 Recent Google Drive Links")
            # Show last 5 processed emails as quick access buttons
            for email_result in list(reversed(st.session_state.processed_emails))[:5]:
                metadata = email_result.get('email_metadata', {})
                subject = metadata.get('subject', 'Unknown')[:25] + "..." if len(metadata.get('subject', '')) > 25 else metadata.get('subject', 'Unknown')
                drive_link = email_result.get('drive_link')
                
                if drive_link:
                    st.markdown(f"""
                    <div style="margin: 5px 0;">
                        <a href="{drive_link}" target="_blank" style="
                            background: #e8f5e8;
                            color: #2d5a2d;
                            padding: 8px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-size: 12px;
                            display: block;
                            border: 1px solid #c8e6c9;
                        ">
                            📁 {subject}
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Auto-refresh section
        st.subheader("🔄 Auto Refresh")
        if st.session_state.processor:
            st.info("Auto-refreshing every 30 seconds...")
            time.sleep(30)
            st.rerun()
        else:
            st.warning("Connect to enable auto-refresh")

if __name__ == "__main__":
    main()

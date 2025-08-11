#!/usr/bin/env python3
"""
Debug script to test email processing independently
"""

import os
import sys
import logging
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'engines'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'invoice_reader'))

from integrated_email_invoice_processor import IntegratedEmailInvoiceProcessor

# Configure logging to see detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_email_processing():
    """Test the email processing functionality"""
    print("🧪 Starting Email Processing Debug Test")
    print("=" * 50)
    
    # Initialize processor
    email = "canspirittest@gmail.com"
    password = "ylyh hkml dgxn vdpi"
    
    print(f"📧 Connecting to: {email}")
    processor = IntegratedEmailInvoiceProcessor(email, password)
    
    try:
        # Connect to email
        print("🔌 Connecting to email server...")
        processor.connect()
        print("✅ Connected successfully!")
        
        # Check for emails
        print("🔍 Checking for emails...")
        results = processor.check_and_process_emails()
        
        print(f"📊 Results: Found {len(results)} processed emails")
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n📧 Email {i}:")
                print(f"   Subject: {result['email_metadata']['subject']}")
                print(f"   From: {result['email_metadata']['from']}")
                print(f"   Invoice Data: {len(result['invoice_data'])} items")
                print(f"   Drive Link: {result['drive_link']}")
                
                # Show invoice data details
                if result['invoice_data']:
                    print("   Invoice Items:")
                    for item in result['invoice_data'][:3]:  # Show first 3 items
                        print(f"     - {item.get('Description', 'N/A')}: {item.get('Amount', 'N/A')}")
                else:
                    print("   ⚠️ No invoice data extracted!")
        else:
            print("ℹ️ No emails found or processed")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 Debug test completed")

if __name__ == "__main__":
    test_email_processing()

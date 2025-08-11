#!/usr/bin/env python3
"""
Email Connection Test Utility

This script tests Gmail IMAP connection with your credentials.
Run this to verify your Gmail setup before using the main application.
"""

import imaplib
import getpass
import sys

def test_email_connection():
    """Test Gmail IMAP connection with user credentials"""
    
    print("📧 Gmail Connection Test")
    print("=" * 30)
    print("\n🔐 This test will verify your Gmail IMAP connection")
    print("⚠️  Use your Gmail App Password, NOT your regular password!")
    print("\n📋 If you don't have an App Password:")
    print("1. Go to: https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification")
    print("3. Generate App Password for 'Mail'")
    print("4. Use the 16-character password here")
    print("\n" + "=" * 50)
    
    # Get credentials from user
    email_address = input("\n📧 Enter your Gmail address: ").strip()
    
    if not email_address:
        print("❌ Email address cannot be empty")
        return False
    
    if not email_address.endswith('@gmail.com'):
        print("❌ Please use a Gmail address (ending with @gmail.com)")
        return False
    
    print("\n🔑 Enter your Gmail App Password:")
    print("   (16 characters like: abcd efgh ijkl mnop)")
    app_password = getpass.getpass("App Password: ").strip()
    
    if not app_password:
        print("❌ App password cannot be empty")
        return False
    
    if len(app_password.replace(' ', '')) != 16:
        print("⚠️  Warning: App passwords are usually 16 characters")
        print("   Continuing with provided password...")
    
    print("\n🔄 Testing connection...")
    print("=" * 30)
    
    try:
        # Test IMAP connection
        print("1. Connecting to Gmail IMAP server...")
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        print("   ✅ Connected to imap.gmail.com")
        
        print("2. Authenticating with credentials...")
        imap.login(email_address, app_password)
        print("   ✅ Authentication successful")
        
        print("3. Selecting inbox...")
        imap.select("inbox")
        print("   ✅ Inbox selected")
        
        print("4. Testing email search...")
        status, messages = imap.search(None, "ALL")
        if status == "OK":
            message_count = len(messages[0].split()) if messages[0] else 0
            print(f"   ✅ Found {message_count} emails in inbox")
        else:
            print("   ⚠️  Search test returned unexpected status")
        
        print("5. Closing connection...")
        imap.logout()
        print("   ✅ Connection closed properly")
        
        print("\n🎉 Gmail connection test successful!")
        print("\n📋 Your credentials are working correctly:")
        print(f"   📧 Email: {email_address}")
        print(f"   🔑 App Password: {'*' * (len(app_password) - 4) + app_password[-4:]}")
        print("\n✨ You can now use these credentials in the main application!")
        
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"\n❌ IMAP Error: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Verify you're using an App Password, not your regular password")
        print("2. Check that 2-Step Verification is enabled on your Google account")
        print("3. Ensure IMAP is enabled in Gmail settings:")
        print("   Go to: https://mail.google.com/mail/u/0/#settings/fwdandpop")
        print("4. Try generating a new App Password")
        return False
        
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check your internet connection")
        print("2. Verify Gmail address is correct")
        print("3. Ensure firewall isn't blocking IMAP (port 993)")
        print("4. Try again in a few minutes (temporary server issues)")
        return False

def main():
    """Main function to run the test"""
    try:
        success = test_email_connection()
        
        if success:
            print("\n" + "=" * 50)
            print("🚀 Ready to run the main application!")
            print("   Use: python -m streamlit run email_invoice_dashboard.py")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("❌ Please fix the issues above before proceeding")
            print("=" * 50)
        
        return success
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

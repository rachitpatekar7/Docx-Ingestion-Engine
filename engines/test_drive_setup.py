#!/usr/bin/env python3
"""
Google Drive Setup Test Utility

This script tests if Google Drive API credentials are properly configured.
Run this before using the main application to verify Drive integration works.
"""

import os
import sys
import json

# Add path for imports
sys.path.append(os.path.dirname(__file__))

def test_drive_setup():
    """Test Google Drive API setup and authentication"""
    
    print("🔍 Testing Google Drive API Setup...")
    print("=" * 50)
    
    # Check if credentials.json exists
    credentials_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
    
    if not os.path.exists(credentials_path):
        print("❌ Error: credentials.json file not found!")
        print(f"   Expected location: {os.path.abspath(credentials_path)}")
        print("\n📋 To fix this:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create or select a project")
        print("3. Enable Google Drive API")
        print("4. Create service account credentials")
        print("5. Download the JSON file as 'credentials.json'")
        print("6. Place it in the project root folder")
        return False
    
    print("✅ credentials.json file found")
    
    # Validate credentials file format
    try:
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds_data]
        
        if missing_fields:
            print(f"❌ Error: credentials.json is missing required fields: {missing_fields}")
            print("\n📋 Please re-download the credentials file from Google Cloud Console")
            return False
        
        if creds_data.get('type') != 'service_account':
            print("❌ Error: credentials.json should be for a service account")
            print("\n📋 Please create service account credentials, not OAuth credentials")
            return False
        
        print(f"✅ Valid service account credentials for: {creds_data.get('client_email')}")
        print(f"✅ Project ID: {creds_data.get('project_id')}")
        
    except json.JSONDecodeError:
        print("❌ Error: credentials.json is not valid JSON")
        print("\n📋 Please re-download the credentials file")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials.json: {e}")
        return False
    
    # Test Google Drive API import
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        print("✅ Google API libraries imported successfully")
    except ImportError as e:
        print(f"❌ Error: Missing Google API libraries: {e}")
        print("\n📋 To fix this, run:")
        print("pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False
    
    # Test authentication
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        
        # Build Drive service
        service = build('drive', 'v3', credentials=credentials)
        
        # Test API call - list files (limited to 1 to minimize API usage)
        results = service.files().list(pageSize=1).execute()
        
        print("✅ Successfully authenticated with Google Drive API")
        print(f"✅ API test successful - Drive connection working")
        
    except Exception as e:
        print(f"❌ Error connecting to Google Drive API: {e}")
        print("\n📋 Possible fixes:")
        print("1. Verify the service account email has access to Google Drive")
        print("2. Share a Google Drive folder with the service account email")
        print("3. Check that Google Drive API is enabled in your Google Cloud project")
        print("4. Verify your internet connection")
        return False
    
    print("\n🎉 Google Drive setup test completed successfully!")
    print("\n📋 Next steps:")
    print("1. Create a folder in Google Drive called 'Email Invoice Processing'")
    print(f"2. Share it with: {creds_data.get('client_email')}")
    print("3. Give the service account 'Editor' permissions")
    print("4. Your system is ready to upload files to Google Drive!")
    
    return True

if __name__ == "__main__":
    success = test_drive_setup()
    sys.exit(0 if success else 1)

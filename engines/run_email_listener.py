# engines/run_email_listener.py

import sys
from email_listener import EmailListener

# Default credentials (can be overridden by command line arguments)
DEFAULT_EMAIL = "canspirittest@gmail.com"
DEFAULT_APP_PASSWORD = "ylyh hkml dgxn vdpi"

if __name__ == "__main__":
    # Check if email and password are provided as command line arguments
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        app_password = sys.argv[2]
        print(f"[INFO] Using provided credentials for {email}")
    else:
        email = DEFAULT_EMAIL
        app_password = DEFAULT_APP_PASSWORD
        print(f"[INFO] Using default credentials for {email}")
    
    print(f"[INFO] Starting email listener...")
    print(f"[INFO] Email: {email}")
    print(f"[INFO] Connecting to Gmail...")
    
    try:
        listener = EmailListener(email, app_password)
        print(f"[INFO] Email listener created successfully")
        
        listener.connect()
        print(f"[SUCCESS] Connected to Gmail successfully")
        
        print(f"[INFO] Starting to listen for emails (checking every 60 seconds)...")
        listener.listen(interval=60)
        
    except Exception as e:
        print(f"[ERROR] Failed to start email listener: {str(e)}")
        sys.exit(1)

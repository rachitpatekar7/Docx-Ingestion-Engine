import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import uuid

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_drive():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CREDENTIALS_PATH = os.path.join(BASE_DIR, "oauth2.json")
    token_path = os.path.join(BASE_DIR, 'token.pickle')

    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def create_drive_folder(service, folder_name):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def upload_file(service, filepath, filename, folder_id=None):
    file_metadata = {'name': filename}
    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaFileUpload(filepath, resumable=True)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    print(f"✅ Uploaded: {filename} (ID: {file.get('id')})")

def save_email_and_attachments(to, cc, subject, body, attachments_dir):
    service = authenticate_drive()

    # Create a unique folder per email
    folder_name = f"Email_{uuid.uuid4().hex[:8]}"
    folder_id = create_drive_folder(service, folder_name)
    print(f"📁 Created folder: {folder_name}")

    # Step 1: Save email metadata to a .txt file
    metadata_text = f"""To: {to}
Cc: {cc}
Subject: {subject}

Body:
{body}
"""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_metadata_path = os.path.join(BASE_DIR, 'email_metadata.txt')
    with open(temp_metadata_path, 'w', encoding='utf-8') as f:
        f.write(metadata_text)

    # Upload metadata file
    upload_file(service, temp_metadata_path, "email_metadata.txt", folder_id)
    os.remove(temp_metadata_path)

    # Step 2: Upload each attachment file
    if os.path.exists(attachments_dir):
        for filename in os.listdir(attachments_dir):
            full_path = os.path.join(attachments_dir, filename)
            if os.path.isfile(full_path):
                upload_file(service, full_path, filename, folder_id)
    else:
        print(f"⚠️ Attachments directory not found: {attachments_dir}")

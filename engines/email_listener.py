import os
import time
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta

from drive_uploader import save_email_and_attachments

class EmailListener:
    def __init__(self, email_address, app_password):
        self.email_address = email_address
        self.app_password = app_password
        self.imap = None
        self.seen_uids = set()

    def connect(self):
        print("[CONNECT] Connecting to Gmail via IMAP...")
        self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
        self.imap.login(self.email_address, self.app_password)
        self.imap.select("inbox")
        print("[SUCCESS] Connected.")

    def is_insurance_email(self, msg):
        subject = msg["Subject"]
        if subject:
            decoded_subject, encoding = decode_header(subject)[0]
            if isinstance(decoded_subject, bytes):
                decoded_subject = decoded_subject.decode(encoding or "utf-8", errors="ignore")
            keywords = ["insurance", "policy", "premium", "claim", "renewal"]
            return any(keyword in decoded_subject.lower() for keyword in keywords)
        return False

    def get_decoded(self, header_val):
        decoded_parts = decode_header(header_val)
        decoded_string = ''
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += part
        return decoded_string

    def extract_email_data(self, msg):
        to = msg.get("To", "")
        cc = msg.get("Cc", "")
        subject = self.get_decoded(msg.get("Subject", ""))
        body = ""

        # Extract body (text/plain or fallback to text/html)
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" not in content_disposition and content_type in ("text/plain", "text/html"):
                    charset = part.get_content_charset() or "utf-8"
                    body = part.get_payload(decode=True).decode(charset, errors="ignore")
                    break
        else:
            charset = msg.get_content_charset() or "utf-8"
            body = msg.get_payload(decode=True).decode(charset, errors="ignore")

        return to, cc, subject, body.strip()

    def save_attachments(self, msg):
        attachment_dir = os.path.join("attachments", f"email_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        os.makedirs(attachment_dir, exist_ok=True)
        attachment_found = False

        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get("Content-Disposition") is None:
                continue

            filename = part.get_filename()
            if filename:
                decoded_name, encoding = decode_header(filename)[0]
                if isinstance(decoded_name, bytes):
                    filename = decoded_name.decode(encoding or "utf-8", errors="ignore")

                filepath = os.path.join(attachment_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))

                print(f"[ATTACH] Saved attachment: {filename}")
                attachment_found = True

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

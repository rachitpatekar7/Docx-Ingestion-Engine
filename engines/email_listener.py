# email_listener.py

import imaplib
import email
from email.header import decode_header
import time

class EmailListener:
    def __init__(self, email_user, email_pass, mail_server='imap.gmail.com'):
        self.email_user = email_user
        self.email_pass = email_pass
        self.mail_server = mail_server
        self.mail = None

    def connect(self):
        self.mail = imaplib.IMAP4_SSL(self.mail_server)
        self.mail.login(self.email_user, self.email_pass)
        self.mail.select('inbox')

    def fetch_emails(self):
        status, messages = self.mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()
        emails = []
        
        for e_id in email_ids:
            _, msg = self.mail.fetch(e_id, '(RFC822)')
            msg = email.message_from_bytes(msg[0][1])
            emails.append(self.parse_email(msg))
        
        return emails

    def parse_email(self, msg):
        subject, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8')
        from_ = msg.get('From')
        return {'subject': subject, 'from': from_}

    def listen(self, interval=60):
        while True:
            emails = self.fetch_emails()
            if emails:
                for email in emails:
                    print(f"New email from {email['from']}: {email['subject']}")
            time.sleep(interval)

    def close(self):
        self.mail.logout()
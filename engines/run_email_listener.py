# engines/run_email_listener.py

from email_listener import EmailListener

EMAIL = "YOUREMAIL@gmail.com" #Enter your email address
APP_PASSWORD = "your app password" #Enter your app password

if __name__ == "__main__":
    listener = EmailListener(EMAIL, APP_PASSWORD)
    listener.connect()
    listener.listen(interval=60)

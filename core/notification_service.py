import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import date, datetime

class NotificationService:
    def __init__(self, email_config, storage_file="data/subscribers.json"):
        self.email_config = email_config
        self.storage_file = storage_file
        self.subscribers = self._load_subscribers()

    def _load_subscribers(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    
                    # Check if the file is from today
                    last_date = data.get("date")
                    if last_date == str(date.today()):
                        return data.get("subscribers", {})
            except Exception as e:
                print(f"Warning: Could not load subscribers ({e})")
        return {} # Empty if not from today or doesn't exist

    def _save_subscribers(self):
        with open(self.storage_file, 'w') as f:
            json.dump({
                "date": str(date.today()),
                "subscribers": self.subscribers
            }, f, indent=4)

    def add_subscriber(self, contact_info, theme_name):
        """Adds a subscriber for a specific theme for today."""
        # Ensure we're working with today's list before adding
        current_date_str = str(date.today())
        
        # We need to reload just in case the date has changed since the service was created
        if not os.path.exists(self.storage_file):
            self.subscribers = {}
        else:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                if data.get("date") != current_date_str:
                    self.subscribers = {} # Clear if day changed
                
        if theme_name not in self.subscribers:
            self.subscribers[theme_name] = []
            
        if contact_info not in self.subscribers[theme_name]:
            self.subscribers[theme_name].append(contact_info)
            self._save_subscribers()
            print(f"Added {contact_info} to {theme_name} notifications for today.")
            return True
        return False

    def send_notification(self, theme_name, message):
        """Sends a notification to all subscribers of a theme."""
        # Reload to ensure day is valid
        self.subscribers = self._load_subscribers()
        
        targets = self.subscribers.get(theme_name, [])
        if not targets:
            print(f"No subscribers for {theme_name}.")
            return
            
        server = os.getenv("SMTP_SERVER") or self.email_config.get("smtp_server")
        port = int(os.getenv("SMTP_PORT", self.email_config.get("smtp_port", 587)))
        sender = os.getenv("SMTP_SENDER_EMAIL") or self.email_config.get("sender_email")
        password = os.getenv("SMTP_SENDER_PASSWORD") or self.email_config.get("sender_password")
        
        if not server or not sender or not password:
            print("Warning: SMTP configuration is incomplete. Cannot send notifications.")
            return
            
        try:
            # We open a connection once and send all emails
            with smtplib.SMTP(server, port) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(sender, password)
                
                for target in targets:
                    msg = MIMEText(message)
                    msg['Subject'] = f"Groundskeeper: {theme_name} Update"
                    msg['From'] = sender
                    msg['To'] = target
                    
                    smtp.send_message(msg)
                    print(f"Notification sent to {target} for {theme_name}.")
        except Exception as e:
            print(f"Failed to send email notifications: {e}")

    def send_test_email(self):
        """Sends a test email to the sender's own email to verify SMTP settings."""
        server = os.getenv("SMTP_SERVER") or self.email_config.get("smtp_server")
        port = int(os.getenv("SMTP_PORT", self.email_config.get("smtp_port", 587)))
        sender = os.getenv("SMTP_SENDER_EMAIL") or self.email_config.get("sender_email")
        password = os.getenv("SMTP_SENDER_PASSWORD") or self.email_config.get("sender_password")
        
        if not server or not sender or not password:
            print("Warning: SMTP configuration is incomplete. Cannot send test notification.")
            return False, "SMTP config is incomplete."
            
        try:
            with smtplib.SMTP(server, port) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(sender, password)
                
                msg = MIMEText("This is a test notification from Groundskeeper to verify your email setup.")
                msg['Subject'] = "Groundskeeper: Test Email"
                msg['From'] = sender
                msg['To'] = sender # Send to self
                
                smtp.send_message(msg)
                print(f"Test notification sent to {sender}.")
                return True, "Test email sent successfully!"
        except Exception as e:
            error_msg = str(e)
            print(f"Failed to send test email: {error_msg}")
            return False, error_msg

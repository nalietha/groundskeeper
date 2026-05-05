import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime
import jinja2

class NotificationService:
    def __init__(self, email_config, storage_file="data/subscribers.json"):
        self.email_config = email_config
        self.storage_file = storage_file
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(os.path.dirname(current_dir), 'templates', 'notifications')
        self.jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

        self.subscribers = self._load_subscribers()

    def _load_subscribers(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    # Support both the old format (dict with 'subscribers') and the new format
                    if "subscribers" in data:
                        return data.get("subscribers", {})
                    return data
            except Exception as e:
                print(f"Warning: Could not load subscribers ({e})")
        return {}

    def _save_subscribers(self):
        with open(self.storage_file, 'w') as f:
            json.dump({"subscribers": self.subscribers}, f, indent=4)

    def add_subscriber(self, contact_info, theme_name, alias="Friend", days=None):
        if days is None:
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            
        self.subscribers = self._load_subscribers()
        
        if theme_name not in self.subscribers:
            self.subscribers[theme_name] = []
            
        # Check if they exist. If they do, UPDATE their days. 
        for sub in self.subscribers[theme_name]:
            if isinstance(sub, dict) and sub.get("contact") == contact_info:
                sub['alias'] = alias
                sub['days'] = days
                self._save_subscribers()
                print(f"Updated {alias}'s schedule for {theme_name}.")
                return True
            elif sub == contact_info: # Fallback for old string-based data
                self.subscribers[theme_name].remove(sub)
                break
                
        # If new, append them
        self.subscribers[theme_name].append({"contact": contact_info, "alias": alias, "days": days})
        self._save_subscribers()
        print(f"Added {alias} ({contact_info}) to {theme_name} notifications for {days}.")
        return True

    def send_notification(self, theme_name, context, test_mode=False):
        server = os.getenv("SMTP_SERVER") or self.email_config.get("smtp_server")
        port = int(os.getenv("SMTP_PORT", self.email_config.get("smtp_port", 587)))
        sender = os.getenv("SMTP_SENDER_EMAIL") or self.email_config.get("sender_email")
        password = os.getenv("SMTP_SENDER_PASSWORD") or self.email_config.get("sender_password")
        
        if not server or not sender or not password:
            print("Warning: SMTP configuration is incomplete.")
            return

        current_day = datetime.now().strftime("%A") # e.g., "Tuesday"

        if test_mode:
            # If testing, force the day to be today so it sends
            targets = [{"contact": sender, "alias": "Tester", "days": [current_day]}]
        else:
            self.subscribers = self._load_subscribers()
            all_targets = self.subscribers.get(theme_name, [])
            
            # FILTER targets: Only include people who have "Today" in their schedule
            targets = []
            for t in all_targets:
                if isinstance(t, dict):
                    if current_day in t.get("days", []):
                        targets.append(t)
                else:
                    # Legacy fallback
                    targets.append({"contact": t, "alias": "Friend", "days": [current_day]})
            
            if not targets:
                print(f"No subscribers scheduled for {current_day} for {theme_name}.")
                return
            
        try:
            with smtplib.SMTP(server, port) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(sender, password)
                
                template = self.jinja_env.get_template('email_alert.html')
                
                for target in targets:
                    contact = target.get("contact")
                    alias = target.get("alias", "Friend")
                    
                    target_context = context.copy()
                    target_context["alias"] = alias
                    
                    html_body = template.render(**target_context)
                    
                    msg = MIMEMultipart("alternative")
                    msg['Subject'] = f"Groundskeeper: {theme_name} Update"
                    msg['From'] = sender
                    msg['To'] = contact
                    
                    msg.attach(MIMEText(context.get('main_message', ''), "plain"))
                    msg.attach(MIMEText(html_body, "html"))
                    
                    smtp.send_message(msg)
                    print(f"Notification sent to {contact} for {theme_name}.")
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

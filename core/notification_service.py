import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime
from urllib.parse import quote
import jinja2

from core.utils import get_local_ip

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

    @staticmethod
    def _contact_of(sub):
        """Extracts the contact string from a subscriber entry (dict or legacy string)."""
        return sub.get("contact") if isinstance(sub, dict) else sub

    def remove_subscriber(self, contact_info, theme_name):
        """Removes a contact from a single theme. Returns True if a subscription was removed."""
        self.subscribers = self._load_subscribers()
        if theme_name not in self.subscribers:
            return False

        original = self.subscribers[theme_name]
        remaining = [s for s in original if self._contact_of(s) != contact_info]
        removed = len(remaining) < len(original)

        if remaining:
            self.subscribers[theme_name] = remaining
        else:
            # Tidy up themes that no longer have any subscribers.
            del self.subscribers[theme_name]

        if removed:
            self._save_subscribers()
            print(f"Removed {contact_info} from {theme_name} notifications.")
        return removed

    def remove_all_subscriptions(self, contact_info):
        """Removes a contact from every theme. Returns the list of themes they were removed from."""
        self.subscribers = self._load_subscribers()
        removed_from = []

        for theme_name in list(self.subscribers.keys()):
            original = self.subscribers[theme_name]
            remaining = [s for s in original if self._contact_of(s) != contact_info]
            if len(remaining) < len(original):
                removed_from.append(theme_name)
            if remaining:
                self.subscribers[theme_name] = remaining
            else:
                del self.subscribers[theme_name]

        if removed_from:
            self._save_subscribers()
            print(f"Removed {contact_info} from all notifications: {removed_from}.")
        return removed_from

    def get_subscriptions_for(self, contact_info):
        """Returns the subscriptions for a contact as a list of
        {theme_name, alias, days} dicts (across every theme)."""
        self.subscribers = self._load_subscribers()
        results = []
        for theme_name, subs in self.subscribers.items():
            for sub in subs:
                if self._contact_of(sub) != contact_info:
                    continue
                if isinstance(sub, dict):
                    results.append({
                        "theme_name": theme_name,
                        "alias": sub.get("alias", "Friend"),
                        "days": sub.get("days", []),
                    })
                else:  # legacy bare-string entry
                    results.append({"theme_name": theme_name, "alias": "Friend", "days": []})
        return results

    def _resolve_smtp_config(self):
        """Resolves SMTP settings from the environment, falling back to email_config.

        Returns a ``(server, port, sender, password)`` tuple, or ``None`` if any
        required field is missing.
        """
        server = os.getenv("SMTP_SERVER") or self.email_config.get("smtp_server")
        port = int(os.getenv("SMTP_PORT", self.email_config.get("smtp_port", 587)))
        sender = os.getenv("SMTP_SENDER_EMAIL") or self.email_config.get("sender_email")
        password = os.getenv("SMTP_SENDER_PASSWORD") or self.email_config.get("sender_password")

        if not server or not sender or not password:
            return None
        return server, port, sender, password

    def _connect_smtp(self, server, port, sender, password):
        """Opens an authenticated SMTP session. Caller is responsible for closing it."""
        smtp = smtplib.SMTP(server, port)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(sender, password)
        return smtp

    def send_notification(self, theme_name, context, test_mode=False):
        smtp_config = self._resolve_smtp_config()
        if smtp_config is None:
            print("Warning: SMTP configuration is incomplete.")
            return
        server, port, sender, password = smtp_config

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
            
        webapp_port = int(os.getenv("WEBAPP_PORT", 5000))
        base_url = f"http://{get_local_ip()}:{webapp_port}"

        try:
            with self._connect_smtp(server, port, sender, password) as smtp:
                template = self.jinja_env.get_template('email_alert.html')

                for target in targets:
                    contact = target.get("contact")
                    alias = target.get("alias", "Friend")

                    target_context = context.copy()
                    target_context["alias"] = alias
                    # One-click unsubscribe link for this specific recipient/theme.
                    target_context["unsubscribe_url"] = (
                        f"{base_url}/unsubscribe?contact={quote(contact)}&theme={quote(theme_name)}"
                    )

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
        smtp_config = self._resolve_smtp_config()
        if smtp_config is None:
            print("Warning: SMTP configuration is incomplete. Cannot send test notification.")
            return False, "SMTP config is incomplete."
        server, port, sender, password = smtp_config

        try:
            with self._connect_smtp(server, port, sender, password) as smtp:
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

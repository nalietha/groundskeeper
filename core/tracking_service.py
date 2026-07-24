import json
import uuid
from datetime import datetime

from core.utils import load_json

class TrackingService:
   
    def __init__(self, state_file, theme_service, joke_service=None, affirmation_service=None, newsletter_service=None):
        self.state_file = state_file
        self.theme_service = theme_service
        self.joke_service = joke_service
        self.affirmation_service = affirmation_service
        self.newsletter_service = newsletter_service # Add this
        
        self.tracked_items = self._load_tracked_items()
        
        # Load the last newsletter date from the state file
        self.last_newsletter_date = None
        self._load_newsletter_state()

    def _load_newsletter_state(self):
        data = load_json(self.state_file, default={})
        self.last_newsletter_date = data.get('last_newsletter_date')

    def _load_tracked_items(self):
        """Loads items from the state file, converting timestamps back to datetime objects."""
        data = load_json(self.state_file, default={})
        items_data = data.get('tracked_items', [])
        for item in items_data:
            if 'start_time' in item and item['start_time']:
                item['start_time'] = datetime.fromisoformat(item['start_time'])
        return items_data

    def _save_tracked_items(self):
        items_to_save = []
        for item in self.tracked_items:
            item_copy = item.copy()
            if 'start_time' in item_copy and item_copy['start_time']:
                item_copy['start_time'] = item_copy['start_time'].isoformat()
            items_to_save.append(item_copy)

        with open(self.state_file, 'w') as f:
            json.dump({
                'tracked_items': items_to_save,
                'last_newsletter_date': self.last_newsletter_date # Add this
            }, f, indent=4)

    def start_tracking_item(self, theme_name, custom_timer=None):
        """Starts tracking a new item, replacing an existing one of the same theme."""
        self.tracked_items = [item for item in self.tracked_items if item['theme_name'] != theme_name]

        theme = self.theme_service.get_theme(theme_name)
        if theme:
            new_item = {
                "id": str(uuid.uuid4()),
                "theme_name": theme_name,
                "start_time": datetime.now(),
                "mood_tier_name": None,
                "notified_events": [] # Track what notifications have been sent
            }
            self.tracked_items.append(new_item)
            self._save_tracked_items()
            print(f"Started tracking new item: {theme_name}")
            return new_item
        return None

    def get_tracked_items(self):
        """Returns the list of all currently tracked items."""
        return self.tracked_items

    def reset_all_items(self):
        """Clears all tracked items and saves the state."""
        self.tracked_items = []
        self._save_tracked_items()
        print("All tracked items have been reset.")
        
    def _get_newsletter_content(self, theme):
        """Fetches basic notification content, delegating composition to the
        newsletter service (which owns how content is assembled)."""
        if self.newsletter_service:
            return self.newsletter_service.get_basic_content(theme)
        return {}

    def check_notifications(self, notification_service):
        now = datetime.now()
        state_changed = False
        
        for item in self.tracked_items:
            theme = self.theme_service.get_theme(item['theme_name'])
            if not theme: continue
            
            elapsed_ms = (now - item['start_time']).total_seconds() * 1000
            events = item.get('notified_events', [])
            timer_ms = getattr(theme, 'timer_ms', 0)
            
           # 1. Started Notification
            if 'started' not in events:
                if timer_ms > 0 and elapsed_ms >= timer_ms:
                    # Skip 'started' notification if it's already 'ready'
                    events.append('started')
                    item['notified_events'] = events
                    state_changed = True
                else:
                    msg = f"{theme.name} has just been started!"
                    context = {"theme_name": theme.name, "main_message": msg}
                    
                    today_str = str(now.date())
                    # Only append the newsletter if it's the first brew of the day
                    if self.newsletter_service and self.last_newsletter_date != today_str:
                        newsletter_content = self.newsletter_service.generate_morning_newsletter(theme)
                        context.update(newsletter_content)
                        
                        # Mark today as sent!
                        self.last_newsletter_date = today_str
                        state_changed = True

                    notification_service.send_notification(theme.name, context)
                    events.append('started')
                    item['notified_events'] = events
                    state_changed = True
                
            # 2. Ready Notification
            if timer_ms > 0 and elapsed_ms >= timer_ms and 'ready' not in events:
                hour = now.hour
                time_of_day = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening" if hour < 21 else "nighttime"
                    
                context = {
                    "theme_name": theme.name,
                    "main_message": f"{theme.name} is now ready! Enjoy your {time_of_day} cuppa!"
                }
                context.update(self._get_newsletter_content(theme))
                
                notification_service.send_notification(theme.name, context)
                events.append('ready')
                item['notified_events'] = events
                state_changed = True
                
        if state_changed:
            self._save_tracked_items()
 
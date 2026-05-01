import json
import uuid
from datetime import datetime

class TrackingService:
    """
    Manages loading, saving, and updating all tracked items.
    """
    def __init__(self, state_file, theme_service, joke_service=None, affirmation_service=None):
        self.state_file = state_file
        self.theme_service = theme_service
        self.joke_service = joke_service
        self.affirmation_service = affirmation_service
        self.tracked_items = self._load_tracked_items()

    def _load_tracked_items(self):
        """Loads items from the state file, converting timestamps back to datetime objects."""
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                items_data = data.get('tracked_items', [])
                for item in items_data:
                    if 'start_time' in item and item['start_time']:
                        item['start_time'] = datetime.fromisoformat(item['start_time'])
                return items_data
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_tracked_items(self):
        """Saves items to the state file, converting datetime objects to strings."""
        items_to_save = []
        for item in self.tracked_items:
            item_copy = item.copy()
            if 'start_time' in item_copy and item_copy['start_time']:
                item_copy['start_time'] = item_copy['start_time'].isoformat()
            items_to_save.append(item_copy)

        with open(self.state_file, 'w') as f:
            json.dump({'tracked_items': items_to_save}, f, indent=4)

    def start_tracking_item(self, theme_name):
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
        
    def _append_newsletter_content(self, message, theme):
        """Appends the joke of the day and daily affirmation to the message."""
        content = message + "\n"
        
        if getattr(self, 'joke_service', None):
            joke = self.joke_service.get_joke(theme=theme)
            if joke:
                content += f"\n\n--- Joke of the Day ---\n{joke}"
                
        if getattr(self, 'affirmation_service', None):
            affirmation = self.affirmation_service.get_daily_affirmation()
            if affirmation:
                content += f"\n\n--- Daily Affirmation ---\n{affirmation}"
                
        return content
        
    def check_notifications(self, notification_service):
        """Checks if any tracked items have reached a notification threshold and sends alerts."""
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
                    # Skip 'started' notification if it's already 'ready' to avoid double emails on restart
                    events.append('started')
                    item['notified_events'] = events
                    state_changed = True
                else:
                    msg = f"Update: {theme.name} has just been started!"
                    if timer_ms <= 0:
                        msg = self._append_newsletter_content(msg, theme)
                        
                    notification_service.send_notification(theme.name, msg)
                    events.append('started')
                    item['notified_events'] = events
                    state_changed = True
                
            # 2. Ready Notification
            if timer_ms > 0 and elapsed_ms >= timer_ms and 'ready' not in events:
                hour = now.hour
                if hour < 12:
                    time_of_day = "morning"
                elif hour < 17:
                    time_of_day = "afternoon"
                elif hour < 21:
                    time_of_day = "evening"
                else:
                    time_of_day = "nighttime"
                    
                msg = f"Update: {theme.name} is now ready! Enjoy your {time_of_day} cuppa!"
                msg = self._append_newsletter_content(msg, theme)
                
                notification_service.send_notification(theme.name, msg)
                events.append('ready')
                item['notified_events'] = events
                state_changed = True
                
        if state_changed:
            self._save_tracked_items()
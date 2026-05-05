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
        
    def _get_newsletter_content(self, theme):
        """Fetches joke and affirmation as a dictionary."""
        content = {}
        if getattr(self, 'joke_service', None):
            content['joke'] = self.joke_service.get_joke(theme=theme)
        if getattr(self, 'affirmation_service', None):
            content['affirmation'] = self.affirmation_service.get_daily_affirmation()
        return content

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
                    events.append('started')
                    item['notified_events'] = events
                    state_changed = True
                else:
                    context = {
                        "theme_name": theme.name,
                        "main_message": f"{theme.name} has just been started!"
                    }
                    if timer_ms <= 0:
                        context.update(self._get_newsletter_content(theme))
                        
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
 
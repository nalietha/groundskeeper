import json
import uuid
from datetime import datetime

class TrackingService:
    """
    Manages loading, saving, and updating all tracked items.
    """
    def __init__(self, state_file, theme_service):
        self.state_file = state_file
        self.theme_service = theme_service
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
        # Remove any existing item of the same theme
        self.tracked_items = [item for item in self.tracked_items if item['theme_name'] != theme_name]

        theme = self.theme_service.get_theme(theme_name)
        if theme:
            new_item = {
                "id": str(uuid.uuid4()),
                "theme_name": theme_name,
                "start_time": datetime.now(),
                "mood_tier_name": None
            }
            self.tracked_items.append(new_item)
            self._save_tracked_items()
            print(f"Started tracking new item: {theme_name}")
            return new_item
        return None

    def get_tracked_items(self):
        """Returns the list of all currently tracked items."""
        return self.tracked_items
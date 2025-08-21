import os
import sys
import json
import urllib.request
import subprocess

class Updater:
    def __init__(self, update_url, version_file='version.json'):
        self.update_url = update_url
        self.version_file = version_file
        self.current_versions = self._load_versions()

    def _load_versions(self):
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r') as f:
                return json.load(f)
        return {"system": "1.0.0", "themes": "1.0.0", "games": "1.0.0"}

    def _save_versions(self):
        with open(self.version_file, 'w') as f:
            json.dump(self.current_versions, f, indent=4)

    def check_for_updates(self):
        try:
            with urllib.request.urlopen(self.update_url) as response:
                latest_versions = json.loads(response.read().decode())
            
            updates = {}
            for component in ["system", "themes", "games"]:
                if latest_versions[component] > self.current_versions[component]:
                    updates[component] = latest_versions[component]
            
            return updates
        except Exception as e:
            print(f"Update check failed: {e}")
            return None

    def apply_update(self, component, new_version):
        print(f"Applying {component} update to version {new_version}...")
        # In a real application, you would download and extract files here.
        # For this example, we'll just simulate the update.
        
        self.current_versions[component] = new_version
        self._save_versions()

        if component == "system":
            print("System update requires a full restart.")
            # Restart the application
            os.execv(sys.executable, ['python'] + sys.argv)
        elif component == "themes":
            print("Theme update requires a quick reset.")
            # This will be handled by the main app to reload themes
        elif component == "games":
            print("Game update applied.")
            # This could trigger a download and installation of game files

        return f"{component.capitalize()} updated to {new_version}"
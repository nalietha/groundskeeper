import os
import sys
import json
import urllib.request
import re

class UpdateService:
    def __init__(self, version_file='version.json'):
        self.api_url = "https://api.github.com/repos/nalietha/groundskeeper/releases/latest"
        self.version_file = version_file
        self.current_versions = self._load_versions()
        self.latest_release_info = None

    def _load_versions(self):
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r') as f:
                return json.load(f)
        return {"system": "1.0.0", "themes": "1.0.0", "games": "1.0.0", "jokes": "1.0.0", "affirmations": "1.0.0"}

    def _save_versions(self):
        with open(self.version_file, 'w') as f:
            json.dump(self.current_versions, f, indent=4)

    def _parse_release_body(self, body):
        # Find a JSON block in the release description
        match = re.search(r'```json\s*(\{.*?\})\s*```', body, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return {}
        return {}

    def check_for_updates(self):
        try:
            with urllib.request.urlopen(self.api_url) as response:
                self.latest_release_info = json.loads(response.read().decode())
            
            # Get system version from git tag
            system_version = self.latest_release_info.get('tag_name', 'v0.0.0').lstrip('v')
            
            # Get other versions from release body
            body_versions = self._parse_release_body(self.latest_release_info.get('body', ''))
            
            latest_versions = {
                "system": system_version,
                "themes": body_versions.get("themes", self.current_versions["themes"]),
                "games": body_versions.get("games", self.current_versions["games"]),
                "jokes": body_versions.get("jokes", self.current_versions["jokes"]),
                "affirmations": body_versions.get("affirmations", self.current_versions["affirmations"])
            }

            updates = {}
            for component, latest_ver in latest_versions.items():
                if latest_ver > self.current_versions.get(component, "0.0.0"):
                    updates[component] = latest_ver
            
            return updates if updates else None
        except Exception as e:
            print(f"Update check failed: {e}")
            return None

    def apply_update(self, component, new_version):
        print(f"Applying {component} update to version {new_version}...")
        
        # Placeholder for download logic
        # In a real app, you would find the correct asset from self.latest_release_info['assets']
        # and download it. For example:
        # asset_url = self.latest_release_info['assets'][0]['browser_download_url']
        # urllib.request.urlretrieve(asset_url, f'{component}_update.zip')
        # Then, you would extract and replace the old files.

        self.current_versions[component] = new_version
        self._save_versions()

        if component == "system":
            print("System update requires a full restart.")
            # This would restart the application after files are replaced
            # os.execv(sys.executable, ['python'] + sys.argv)
        elif component in ["themes", "jokes", "affirmations", "games"]:
            print(f"{component.capitalize()} update applied.")

        return f"{component.capitalize()} updated to {new_version}"
# create_theme.py
import os
import json

def create_theme():
    """
    An interactive helper script to generate a new, blank theme structure
    for the Groundskeeper application.
    """
    print("--- Groundskeeper Theme Creator ---")
    
    # 1. Get the theme name from the user
    theme_name_input = input("Enter the name of your new theme (e.g., 'Sushi' or 'Board Games'): ")
    if not theme_name_input:
        print("\nError: Theme name cannot be empty. Aborting.")
        return

    theme_name_capitalized = theme_name_input.title()
    theme_folder_name = theme_name_input.lower().replace(" ", "_")
    
    # 2. Define all the paths that need to be created
    base_path = os.path.join("themes", theme_folder_name)
    assets_path = os.path.join(base_path, "assets")
    game_assets_path = os.path.join(assets_path, "game_assets")
    loading_path = os.path.join(assets_path, "loading")

    # 3. Check if the theme already exists to prevent overwriting
    if os.path.exists(base_path):
        print(f"\nError: A theme named '{theme_folder_name}' already exists. Aborting.")
        return

    print(f"\nCreating new theme '{theme_name_capitalized}' in '{base_path}'...")

    try:
        # 4. Create the directory structure
        os.makedirs(game_assets_path)
        os.makedirs(loading_path)
        print("  - Created folder structure.")

        # 5. Create the placeholder JSON files with default content
        
        # settings.json
        settings_content = {
            "name": theme_name_capitalized,
            "action_text": "Start Action",
            "start_phrase": "Last Started:",
            "not_started_text": "Not started yet",
            "timer_ms": 3600000,
            "colors": {
                "dim_bg": "#1e1e1e", "dim_fg": "#a9a9a9",
                "bright_bg": "#add8e6", "bright_fg": "#000000"
            },
            "mood_tiers": [
                {"name": "Fresh", "threshold_minutes": 0, "emoji": "✨"},
                {"name": "Good", "threshold_minutes": 60, "emoji": "😊"},
                {"name": "Okay", "threshold_minutes": 180, "emoji": "😐"},
                {"name": "Stale", "threshold_minutes": 360, "emoji": "🤢"},
                {"name": "Ancient", "threshold_minutes": 1440, "emoji": "💀"}
            ]
        }
        with open(os.path.join(base_path, "settings.json"), 'w') as f:
            json.dump(settings_content, f, indent=4)

        # list_{theme}.json
        list_content = {
            "Fresh": [{"catcher": "It's brand new!", "descriptor": "The adventure begins."}],
            "Good": [{"catcher": "Still going strong.", "descriptor": "Enjoying the moment."}],
            "Okay": [{"catcher": "It's alright.", "descriptor": "The initial excitement has faded."}],
            "Stale": [{"catcher": "Getting old.", "descriptor": "Maybe it's time for something new."}],
            "Ancient": [{"catcher": "A relic of the past.", "descriptor": "This has been here forever."}]
        }
        with open(os.path.join(base_path, f"list_{theme_folder_name}.json"), 'w') as f:
            json.dump(list_content, f, indent=4)

        # jokes_{theme}.json
        with open(os.path.join(base_path, f"jokes_{theme_folder_name}.json"), 'w') as f:
            json.dump([], f, indent=4)

        # styled_games.json
        with open(os.path.join(assets_path, "styled_games.json"), 'w') as f:
            json.dump({}, f, indent=4)
        
        print("  - Created placeholder JSON files.")
        
        # 6. Create placeholder text files to explain what to do
        with open(os.path.join(assets_path, "ADD_THEME_CARD_HERE.txt"), 'w') as f:
            f.write("Place your 160x120 theme_card.png file in this folder.")
        with open(os.path.join(assets_path, "ADD_ICON_HERE.txt"), 'w') as f:
            f.write("Place your 64x64 icon.png file in this folder.")
        with open(os.path.join(loading_path, "ADD_LOADING_IMAGES_HERE.txt"), 'w') as f:
            f.write("Place your loading screen images (e.g., loading01.jpg) in this folder.")
        with open(os.path.join(game_assets_path, "ADD_THEMED_GAME_ASSETS_HERE.txt"), 'w') as f:
            f.write("Place themed game assets (e.g., a custom food.png for Snake) in this folder.")
            
        print("  - Created instruction files.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return

    print("\n✅ Success! Your new theme structure has been created.")
    print("\nNext Steps:")
    print("  1. Create your theme card (theme_card.png) and icon (icon.png) and place them in the 'assets' folder.")
    print("  2. Add one or more loading screen images to the 'assets/loading' folder.")
    print("  3. Customize the text and colors in 'settings.json'.")
    print("  4. Fill out the mood sayings in 'list_...json' and add some jokes to 'jokes_...json'.")
    print("  5. Run the main application to see your new theme in the carousel!")


if __name__ == "__main__":
    create_theme()

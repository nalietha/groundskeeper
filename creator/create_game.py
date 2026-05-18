# create_game.py
import os
import json

def create_game():
    """
    An interactive helper script to generate a new, blank game structure
    for the Groundskeeper application.
    """
    print("--- Groundskeeper Game Creator ---")
    
    game_name_input = input("Enter the name of your new game (e.g., 'Space Invaders'): ")
    if not game_name_input:
        print("\nError: Game name cannot be empty. Aborting.")
        return

    game_folder_name = game_name_input.lower().replace(" ", "_")
    game_class_name = "".join(word.title() for word in game_folder_name.split("_"))

    # Get the directory where this script is located (e.g., 'creators/')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the parent directory (the project root)
    project_root = os.path.dirname(script_dir)
    # Construct the correct path to the 'games' folder
    base_path = os.path.join(project_root, "games", game_folder_name)

    assets_path = os.path.join(base_path, "assets")

    if os.path.exists(base_path):
        print(f"\nError: A game named '{game_folder_name}' already exists. Aborting.")
        return

    print(f"\nCreating new game '{game_class_name}' in '{base_path}'...")

    try:
        os.makedirs(assets_path)
        print("  - Created folder structure.")

        # Create manifest.json
        manifest_content = {
            "active": False,
            "name": game_class_name,
            "entry_point": game_class_name,
            "assets": {
                "example_static": {
                    "path": "assets/static_asset.png",
                    "themeable": False,
                    "width": 32,
                    "height": 32
                },
                "example_themeable": {
                    "path": "assets/themeable_asset.png",
                    "themeable": True,
                    "width": 32,
                    "height": 32
                }
            }
        }
        with open(os.path.join(base_path, "manifest.json"), 'w') as f:
            json.dump(manifest_content, f, indent=4)

        # Create a template game.py
        game_py_content = f"""
import pygame

class {game_class_name}:
    def __init__(self, screen_width, screen_height, assets):
        pygame.init()
        self.width = screen_width
        self.height = screen_height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('{game_class_name}')
        self.assets = assets
        print("Game '{game_class_name}' initialized with assets:", assets)

    def game_loop(self):
        print("Starting game loop for {game_class_name}...")
        game_over = False
        while not game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_b:
                        game_over = True
            
            self.screen.fill((20, 20, 40)) # Dark blue background
            pygame.display.update()
        
        pygame.quit()
        return 0 # Return final score
"""
        with open(os.path.join(base_path, "game.py"), 'w') as f:
            f.write(game_py_content)

        print("  - Created placeholder JSON and Python files.")
        
        # Create instruction files
        with open(os.path.join(base_path, "ADD_GAME_CARD_HERE.txt"), 'w') as f:
            f.write("Place your 160x120 game_card.png file in this folder.")
        with open(os.path.join(assets_path, "ADD_ASSETS_HERE.txt"), 'w') as f:
            f.write("Place your asset files (e.g., static_asset.png) in this folder.")
            
        print("  - Created instruction files.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return

    print("\n✅ Success! Your new game structure has been created.")
    print("\nNext Steps:")
    print("  1. Create your game_card.png and place it in the game's root folder.")
    print("  2. Add your static and default themeable assets to the 'assets' folder.")
    print("  3. Customize the 'manifest.json' to define your assets correctly.")
    print("  4. Write your game logic in 'game.py'.")
    print("  5. When you are ready, change 'active': false to 'active': true in manifest.json.")


if __name__ == "__main__":
    create_game()

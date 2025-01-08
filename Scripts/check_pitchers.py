import requests
import sys

# Get the date from command line arguments
if len(sys.argv) > 1:
    date = sys.argv[1]
else:
    print("Error: Date not provided.")
    sys.exit(1)

# API URL for GamePreviews
url = f"https://localhost:44346/api/GamePreviews/{date}"

# Fetch the GamePreviews data
response = requests.get(url, verify=False)  # Assuming SSL certificate is not verified
if response.status_code != 200:
    print(f"Error: Unable to fetch data from {url}. Status code: {response.status_code}")
    sys.exit(1)

game_previews = response.json()

# List to store game IDs with unannounced pitchers
unannounced_games = []

# Check for games with "Unannounced" pitchers
for game in game_previews:
    home_pitcher = game.get("homePitcher")
    away_pitcher = game.get("awayPitcher")
    if home_pitcher == "Unannounced" or away_pitcher == "Unannounced":
        game_id = game.get("id")
        unannounced_games.append(game_id)
        print(f"Game ID: {game_id} has an unannounced pitcher (Home: {home_pitcher}, Away: {away_pitcher})")

# Exit with status 1 if there are unannounced pitchers, otherwise exit with 0
if unannounced_games:
    print("\nOne or more games have unannounced pitchers. Please update them manually in the database.")
    sys.exit(1)
else:
    print("All games have announced pitchers.")
    sys.exit(0)

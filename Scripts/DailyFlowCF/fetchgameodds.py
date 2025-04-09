import requests
import json
import sys
from datetime import datetime
import urllib3

# Disable SSL verification warnings globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Check if a date argument is provided via command line
if len(sys.argv) > 1:
    date = sys.argv[1]  # Use the first argument as the date
else:
    # Fallback to the default date - opening day
    date = '25-04-07'

# API URLs
odds_url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey=cae244ec5ed018e4316521fb277d6800&regions=us&oddsFormat=american"
game_previews_url = f"https://localhost:44346/api/GamePreviews/{date}"

# API key for odds
api_key = "cae244ec5ed018e4316521fb277d6800"

team_name_dict = {
    "Arizona Diamondbacks": "Diamondbacks",
    "Atlanta Braves": "Braves",
    "Baltimore Orioles": "Orioles",
    "Boston Red Sox": "Red Sox",
    "Chicago Cubs": "Cubs",
    "Chicago White Sox": "White Sox",
    "Cincinnati Reds": "Reds",
    "Cleveland Guardians": "Guardians",
    "Colorado Rockies": "Rockies",
    "Detroit Tigers": "Tigers",
    "Houston Astros": "Astros",
    "Kansas City Royals": "Royals",
    "Los Angeles Angels": "Angels",
    "Los Angeles Dodgers": "Dodgers",
    "Miami Marlins": "Marlins",
    "Milwaukee Brewers": "Brewers",
    "Minnesota Twins": "Twins",
    "New York Mets": "Mets",
    "New York Yankees": "Yankees",
    "Oakland Athletics": "Athletics",
    "Philadelphia Phillies": "Phillies",
    "Pittsburgh Pirates": "Pirates",
    "San Diego Padres": "Padres",
    "San Francisco Giants": "Giants",
    "Seattle Mariners": "Mariners",
    "St. Louis Cardinals": "Cardinals",
    "Tampa Bay Rays": "Rays",
    "Texas Rangers": "Rangers",
    "Toronto Blue Jays": "Blue Jays",
    "Washington Nationals": "Nationals"
}

# Step 1: Get the Game Previews for the day
try:
    game_previews_response = requests.get(game_previews_url, verify=False)
    print(f"Game Previews Response: {game_previews_response}")

    # Ensure the response was successful and valid
    if game_previews_response.status_code == 200:
        game_previews = game_previews_response.json()
    else:
        print(f"Error: Received status code {game_previews_response.status_code}")
        print(f"Response content: {game_previews_response.text}")
        game_previews = []
except Exception as e:
    print(f"Exception occurred when getting game previews: {str(e)}")
    game_previews = []

# Step 2: Fetch odds from the odds API
try:
    # Also disable SSL verification for the odds API (though it's likely a public API with valid cert)
    odds_response = requests.get(odds_url, verify=False)
    
    if odds_response.status_code == 200:
        odds_data = odds_response.json()
    else:
        print(f"Error fetching odds: Status code {odds_response.status_code}")
        print(f"Response content: {odds_response.text}")
        odds_data = []
except Exception as e:
    print(f"Exception occurred when getting odds data: {str(e)}")
    odds_data = []

# Function to find odds for a particular team from a bookmaker
def get_odds_for_team(bookmaker, team_name):
    if not bookmaker or 'markets' not in bookmaker or not bookmaker['markets']:
        return None
    
    for outcome in bookmaker['markets'][0]['outcomes']:
        if outcome['name'].lower().strip() == team_name.lower().strip():
            return outcome['price']
    return None

print(f"Total game previews: {len(game_previews)}")
print(f"Total odds entries: {len(odds_data)}")

# Step 3: Iterate over the Game Previews and find matching odds
for game_preview in game_previews:
    home_team = game_preview["homeTeam"]
    away_team = game_preview["awayTeam"]

    # Print home and away teams for debugging
    print(f"Checking game: {away_team} @ {home_team}")

    # Use the team_name_dict to map the short names in game_previews to the full team names from odds_data
    home_team_full = next((full_name for full_name, short_name in team_name_dict.items() if short_name == home_team), None)
    away_team_full = next((full_name for full_name, short_name in team_name_dict.items() if short_name == away_team), None)

    # Debugging: print if the full team names are not found
    if not home_team_full or not away_team_full:
        print(f"Could not find full names for teams {home_team} or {away_team} in the dictionary.")
        continue

    # Find the matching game in the odds data using the full team names
    match_found = False
    for game_odds in odds_data:
        if game_odds["home_team"].lower().strip() == home_team_full.lower().strip() and game_odds["away_team"].lower().strip() == away_team_full.lower().strip():
            print(f"Match found: {away_team} @ {home_team} - Proceeding with odds posting")
            match_found = True
            
            # Find odds from different bookmakers
            fanduel_odds = next((b for b in game_odds['bookmakers'] if b['key'] == 'fanduel'), None)
            draftkings_odds = next((b for b in game_odds['bookmakers'] if b['key'] == 'draftkings'), None)
            betmgm_odds = next((b for b in game_odds['bookmakers'] if b['key'] == 'betmgm'), None)

            # Get odds for home and away teams from each bookmaker
            fanduel_home_odds = get_odds_for_team(fanduel_odds, home_team_full) if fanduel_odds else None
            fanduel_away_odds = get_odds_for_team(fanduel_odds, away_team_full) if fanduel_odds else None
            draftkings_home_odds = get_odds_for_team(draftkings_odds, home_team_full) if draftkings_odds else None
            draftkings_away_odds = get_odds_for_team(draftkings_odds, away_team_full) if draftkings_odds else None
            betmgm_home_odds = get_odds_for_team(betmgm_odds, home_team_full) if betmgm_odds else None
            betmgm_away_odds = get_odds_for_team(betmgm_odds, away_team_full) if betmgm_odds else None

            # Parse the commence_time as a datetime object and extract time (for TimeSpan)
            try:
                game_datetime = datetime.fromisoformat(game_odds["commence_time"].replace("Z", "+00:00"))
                game_time = game_datetime.time()
            except Exception as e:
                print(f"Error parsing game time: {str(e)}")
                game_time = None

            # Step 4: Prepare the payload (aligned with the API's expected structure)
            game_odds_payload = {
                "id": 0,
                "date": game_preview["date"],
                "gameTime": game_preview["time"],
                "homeTeam": home_team,
                "awayTeam": away_team,
                "gamePreviewID": game_preview["id"],  # Keep this, it's the FK to GamePreview
                "fanduelHomeOdds": fanduel_home_odds,
                "fanduelAwayOdds": fanduel_away_odds,
                "draftkingsHomeOdds": draftkings_home_odds,
                "draftkingsAwayOdds": draftkings_away_odds,
                "betmgmHomeOdds": betmgm_home_odds,
                "betmgmAwayOdds": betmgm_away_odds
            }

            # Print the payload for debugging
            print(f"Posting the following data for {home_team} vs {away_team}:")
            print(json.dumps(game_odds_payload, indent=2))

            # Step 5: Post to the GameOdds API
            try:
                post_response = requests.post(
                    'https://localhost:44346/api/GameOdds',
                    headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                    data=json.dumps(game_odds_payload),
                    verify=False  # Disable SSL verification for this request as well
                )

                # Print the response status and content for debugging
                print(f"POST Response Status Code: {post_response.status_code}")
                print(f"POST Response Content: {post_response.text}")

                # If the status code is not 201 (Created) or 200 (OK), print a warning
                if post_response.status_code != 201 and post_response.status_code != 200:
                    print(f"Warning: Failed to post data for {home_team} vs {away_team}. Status code: {post_response.status_code}")
                    print(f"Response: {post_response.text}")
            except Exception as e:
                print(f"Exception occurred during POST request: {str(e)}")
            
            break

    if not match_found:
        print(f"No matching game found for {away_team} @ {home_team} in the odds API data.")

print("Script execution completed.")
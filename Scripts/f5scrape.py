import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import pytz

# URL to scrape
url = 'https://www.sportsbookreview.com/betting-odds/mlb-baseball/money-line/1st-half/?date=2024-09-12'

# Fetch the webpage content
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Find the <script> tag with id "__NEXT_DATA__"
script_tag = soup.find('script', id="__NEXT_DATA__")

if script_tag:
    # Extract the JSON content from the script tag
    json_data = json.loads(script_tag.string)
    
    # Navigate through the JSON to find the game data
    games_data = json_data['props']['pageProps']['oddsTables'][0]['oddsTableModel']['gameRows']
    
    print(f"Found {len(games_data)} games.\n")

    # Define the timezone objects
    utc_timezone = pytz.utc
    est_timezone = pytz.timezone("America/New_York")

    # Loop through each game and extract the required information
    for i, game in enumerate(games_data, 1):
        game_view = game['gameView']
        home_team = game_view['homeTeam']['fullName']
        away_team = game_view['awayTeam']['fullName']
        start_time_utc = game_view['startDate']
        
        # Convert start time from UTC to EST
        game_datetime_utc = datetime.fromisoformat(start_time_utc.replace('Z', '+00:00')).replace(tzinfo=utc_timezone)
        game_datetime_est = game_datetime_utc.astimezone(est_timezone)
        game_date = game_datetime_est.strftime('%Y-%m-%d')
        game_time = game_datetime_est.strftime('%I:%M %p')  # Convert to 12-hour format

        # Extract BetMGM odds
        betmgm_odds = None
        for odds_view in game['oddsViews']:
            if odds_view and odds_view['sportsbook'] == 'betmgm':
                home_odds = odds_view['currentLine']['homeOdds']
                away_odds = odds_view['currentLine']['awayOdds']

                # Create a game object
                game_object = {
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "date": game_date,
                    "time": game_time,
                    "homeOdds": home_odds,
                    "awayOdds": away_odds
                }

                # Print the object for each game
                print(game_object)
                break
else:
    print("No __NEXT_DATA__ found.")

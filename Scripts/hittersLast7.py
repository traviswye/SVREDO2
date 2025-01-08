import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
import time
import urllib3
import argparse
import sys

# Suppress only the insecure request warning for localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create a session object
session = requests.Session()

# Attach the common headers to the session
session.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'text/plain',
    'Connection': 'keep-alive'
})

# Parse command line arguments
parser = argparse.ArgumentParser(description='Process hitter stats.')
parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y-%m-%d'),
                    help='Date for which to fetch game previews. Format depends on API requirements.')
parser.add_argument('--playoff', type=str, default='False',
                    help='Set to True to process only teams playing today. Defaults to False.')

args = parser.parse_args()

# Convert playoff argument to boolean
playoff = args.playoff.lower() == 'true'

# The URL of the page to scrape
url = 'https://www.fantasypros.com/mlb/stats/hitters.php?range=7&page=ALL'
api_base_url = 'https://localhost:44346/api/MLBPlayer/search?'
hitter_last7_api_url = 'https://localhost:44346/api/HitterLast7'  # Replace with your actual API URL
game_preview_api_url = 'https://localhost:44346/api/GamePreviews/{}'

# Team abbreviation mapping dictionary for player data
team_names = {
    "ARI": "ARI", "ATL": "ATL", "BAL": "BAL", "BOS": "BOS",
    "CHC": "CHC", "CWS": "CHW", "CIN": "CIN", "CLE": "CLE",
    "COL": "COL", "DET": "DET", "HOU": "HOU", "KC": "KCR",
    "LAA": "LAA", "LAD": "LAD", "MIA": "MIA", "MIL": "MIL",
    "MIN": "MIN", "NYM": "NYM", "NYY": "NYY", "OAK": "OAK",
    "PHI": "PHI", "PIT": "PIT", "SD": "SDP", "SEA": "SEA",
    "SF": "SFG", "STL": "STL", "TB": "TBR", "TEX": "TEX",
    "TOR": "TOR", "WSH": "WSN"
}

# Team name mapping dictionary for game previews
team_name_to_abbr = {
    "Diamondbacks": "ARI", "Braves": "ATL", "Orioles": "BAL", "Red Sox": "BOS",
    "Cubs": "CHC", "White Sox": "CHW", "Reds": "CIN", "Guardians": "CLE",
    "Rockies": "COL", "Tigers": "DET", "Astros": "HOU", "Royals": "KC",
    "Angels": "LAA", "Dodgers": "LAD", "Marlins": "MIA", "Brewers": "MIL",
    "Twins": "MIN", "Mets": "NYM", "Yankees": "NYY", "Athletics": "OAK",
    "Phillies": "PHI", "Pirates": "PIT", "Padres": "SDP", "Mariners": "SEA",
    "Giants": "SFG", "Cardinals": "STL", "Rays": "TBR", "Rangers": "TEX",
    "Blue Jays": "TOR", "Nationals": "WSN"
}

# Initialize the set of teams playing on the specified date
teams_playing_abbr = set()

if playoff:
    # Use the date provided via command line argument
    date_str = args.date
    # We won't validate the date format since the API may accept different formats
    # We'll use the date string as-is in the API call
    # Fetch game previews for the specified date
    game_preview_url = game_preview_api_url.format(date_str)
    response = session.get(game_preview_url, verify=False)
    if response.status_code == 200:
        game_previews = response.json()
        # Extract teams from game previews
        teams_playing = set()
        for game in game_previews:
            home_team = game.get('homeTeam')
            away_team = game.get('awayTeam')
            teams_playing.add(home_team)
            teams_playing.add(away_team)
        # Map team names to abbreviations
        for team_name in teams_playing:
            team_abbr = team_name_to_abbr.get(team_name)
            if team_abbr:
                teams_playing_abbr.add(team_abbr)
            else:
                print(f"Warning: Team name {team_name} not found in mapping.")
    else:
        print(f"Failed to retrieve game previews: {response.status_code}, {response.text}")
        # If we can't get the game previews, we won't process any players
        teams_playing_abbr = set()

# Send a GET request to the URL
response = session.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
table_body = soup.find('tbody')

players = []
no_bbrefid_players = []

def get_bbref_id(session, full_name, team):
    search_url = f"{api_base_url}fullName={full_name}&team={team}"
    search_response = session.get(search_url, verify=False)
    if search_response.status_code == 200 and search_response.json():
        return search_response.json()[0].get("bbrefId")
    return None

def post_player_data(session, player, retries=3, backoff_factor=2):
    for attempt in range(retries):
        try:
            response = session.post(hitter_last7_api_url, json=player, timeout=30, verify=False)
            print(f"POST request to {hitter_last7_api_url} with payload: {json.dumps(player)}")
            print(f"Response status code: {response.status_code}, Response content: {response.content}")
            
            if response.status_code == 201:
                print(f"Successfully posted data for {player['name']}")
                return
            else:
                print(f"Failed to post data for {player['name']}: {response.status_code}, {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error posting data for {player['name']}: {e}")
        
        # Backoff logic
        sleep_time = backoff_factor ** attempt
        print(f"Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)
    
    print(f"Failed to post data for {player['name']} after {retries} retries.")

for row in table_body.find_all('tr'):
    columns = row.find_all('td')
    if len(columns) == 0:
        continue

    try:
        full_name = columns[1].text.strip().split('(')[0].strip()
        team_abbr_raw = columns[1].text.strip().split('(')[-1].split('-')[0].strip()
        team_abbr = team_names.get(team_abbr_raw, team_abbr_raw)
        team = team_abbr
        
        # Check if the player's team is playing today when playoff flag is True
        if playoff and team not in teams_playing_abbr:
            continue  # Skip this player

        bbrefId = get_bbref_id(session, full_name, team)
        if not bbrefId:
            no_bbrefid_players.append(f"{full_name} {team}")
            continue

        player = {
            "id": 0,
            "bbrefId": bbrefId,
            "dateUpdated": datetime.now().isoformat(),
            "team": team,
            "pos": columns[1].text.strip().split('-')[-1].strip(')').strip(),
            "name": full_name,
            "ab": int(columns[2].text.strip()),
            "r": int(columns[3].text.strip()),
            "hr": int(columns[4].text.strip()),
            "rbi": int(columns[5].text.strip()),
            "sb": int(columns[6].text.strip()),
            "avg": float(columns[7].text.strip()),
            "obp": float(columns[8].text.strip()),
            "h": int(columns[9].text.strip()),
            "twoB": int(columns[10].text.strip()),
            "threeB": int(columns[11].text.strip()),
            "bb": int(columns[12].text.strip()),
            "k": int(columns[13].text.strip()),
            "slg": float(columns[14].text.strip()),
            "ops": float(columns[15].text.strip()),
            "rostered": float(columns[16].text.strip().strip('%'))
        }
        
        players.append(player)
        post_player_data(session, player)

    except (ValueError, IndexError) as e:
        print(f"Skipping player due to incomplete or invalid data: {e}")
        continue

print("Players with bbrefId:")
for player in players:
    print(player)

print("\nPlayers without bbrefId:")
for player_name in no_bbrefid_players:
    print(player_name)

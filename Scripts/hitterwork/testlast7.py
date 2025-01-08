import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
import time

# Create a session object
session = requests.Session()

# Attach the common headers to the session
session.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'text/plain',
    'Connection': 'keep-alive'
})

# The URL of the page to scrape
url = 'https://www.fantasypros.com/mlb/stats/hitters.php?range=7'
api_base_url = 'https://localhost:44346/api/MLBPlayer/search?'
hitter_last7_api_url = 'https://localhost:44346/api/HitterLast7'  # Replace with your actual API URL

# Team abbreviation mapping dictionary
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

    full_name = columns[1].text.strip().split('(')[0].strip()
    team_abbr = columns[1].text.strip().split('(')[-1].split('-')[0].strip()
    team = team_names.get(team_abbr, team_abbr)
    
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
    #time.sleep(1)  # Slight delay to avoid overwhelming the server

print("Players with bbrefId:")
for player in players:
    print(player)

print("\nPlayers without bbrefId:")
for player_name in no_bbrefid_players:
    print(player_name)

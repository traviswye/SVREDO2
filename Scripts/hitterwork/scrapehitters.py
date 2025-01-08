import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

current_datetime = datetime.now().isoformat()  # This will give you the current date and time in ISO format

# Team abbreviation dictionary for all MLB teams
team_abbreviations = {
    'Diamondbacks': 'ARI', 'Braves': 'ATL', 'Orioles': 'BAL', 'Red Sox': 'BOS', 
    'Cubs': 'CHC', 'White Sox': 'CHW', 'Reds': 'CIN', 'Guardians': 'CLE',
    'Rockies': 'COL', 'Tigers': 'DET', 'Astros': 'HOU', 'Royals': 'KCR', 
    'Angels': 'LAA', 'Dodgers': 'LAD', 'Marlins': 'MIA', 'Brewers': 'MIL',
    'Twins': 'MIN', 'Mets': 'NYM', 'Yankees': 'NYY', 'Athletics': 'OAK',
    'Phillies': 'PHI', 'Pirates': 'PIT', 'Padres': 'SDP', 'Mariners': 'SEA',
    'Giants': 'SFG', 'Cardinals': 'STL', 'Rays': 'TBR', 'Rangers': 'TEX',
    'Blue Jays': 'TOR', 'Nationals': 'WSN'
}

# Dictionary mapping teams to their leagues
teamLg = {
    "ARI": "NL", "ATL": "NL", "BAL": "AL", "BOS": "AL", "CHC": "NL", "CHW": "AL",
    "CIN": "NL", "CLE": "AL", "COL": "NL", "DET": "AL", "HOU": "NL", "KCR": "AL",
    "LAA": "AL", "LAD": "NL", "MIA": "NL", "MIL": "NL", "MIN": "AL", "NYM": "NL",
    "NYY": "AL", "OAK": "AL", "PHI": "NL", "PIT": "NL", "SDP": "NL", "SEA": "AL",
    "SFG": "NL", "STL": "NL", "TBR": "AL", "TEX": "AL", "TOR": "AL", "WSN": "NL"
}

def get_league_by_team(team_abbr):
    return teamLg.get(team_abbr, "Unknown")

def get_game_teams(date_str):
    # Fetch games for the given date
    game_previews_url = f"https://localhost:44346/api/GamePreviews/{date_str}"
    print(f"Requesting game previews from: {game_previews_url}")
    
    try:
        response = requests.get(game_previews_url, verify=False)  # Disable SSL verification
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            games = response.json()
            print(f"Games retrieved: {games}")  # Log the games retrieved
            teams = set()
            for game in games:
                home_team = game['homeTeam']
                away_team = game['awayTeam']
                teams.add(home_team)
                teams.add(away_team)
            return teams
        else:
            print(f"Failed to retrieve games for {date_str}. Response content: {response.text}")
            return set()
    except Exception as e:
        print(f"Error occurred while fetching game previews: {e}")
        return set()

# Format the date as yy-MM-dd
today_str = datetime.now().strftime('%y-%m-%d')
teams_with_games = get_game_teams(today_str)

def safe_float_conversion(value, default=0.0):
    try:
        return float(value)
    except ValueError:
        return default

def safe_String_conversion(value, default=''):
    try:
        return string(value)
    except ValueError:
        return default
def safe_int_conversion(value, default=0):
    try:
        return int(value)
    except ValueError:
        return default


def get_team_batting_data(team_name):
    # Get the abbreviation for the team
    team_abbr = team_abbreviations.get(team_name, None)
    if not team_abbr:
        print(f"Team {team_name} not found.")
        return
    
    # Create the URL
    url = f"https://www.baseball-reference.com/teams/{team_abbr}/2024.shtml"
    
    # Fetch the page
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve data for {team_name}")
        return
    
    # Parse the page
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the team batting table
    table = soup.find('table', id='team_batting')
    
    if not table:
        print("Team Batting table not found.")
        return
    
    # Extract the rows of the table
    rows = table.find_all('tr')
    
    headers = [
        "Pos", "Name", "Age", "G", "PA", "AB", "R", "H", "2B", "3B", "HR", "RBI", "SB", "CS", 
        "BB", "SO", "BA", "OBP", "SLG", "OPS", "OPS+", "TB", "GDP", "HBP", "SH", "SF", "IBB", "bbrefID"
    ]
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 0:  # Ensure row has data
            row_data = [cell.getText().strip() for cell in cells]
            # Extract bbrefID from the href attribute in the Name column
            name_cell = row.find('td', {'data-stat': 'player'})
            if name_cell and name_cell.find('a'):
                href = name_cell.find('a')['href']
                bbrefID = href.split('/')[-1].replace('.shtml', '')  # Extract bbrefID
            else:
                bbrefID = None
            
            # Skip rows where Pos is 'P' (pitchers) or bbrefID is None
            if row_data[0].strip() != 'P' and bbrefID is not None:
                # Create a temporary dictionary with player data
                player_data = dict(zip(headers, row_data + [bbrefID]))

                # API endpoint to check if the player exists
                api_urlGET = f"https://localhost:44346/api/Hitters/{bbrefID}"
                api_urlPUT = f"https://localhost:44346/api/Hitters/{bbrefID}"
                api_urlPOST = f"https://localhost:44346/api/Hitters"

                # Check if the player exists (GET request)
                response = requests.get(api_urlGET, verify=False)  # Disable SSL verification
                
                if response.status_code == 200:
                    # Player exists, perform a PUT request
                    existing_data = response.json()
                    
                    # Prepare the PUT payload
                    put_payload = {
                        "bbrefId": bbrefID,
                        "name": player_data["Name"],
                        "age": int(player_data["Age"]),
                        "year": 2024,
                        "team": team_abbr,
                        "lg": get_league_by_team(team_abbr),
                        "war": existing_data["war"],
                        "g": safe_int_conversion(player_data["G"]),
                        "pa": safe_int_conversion(player_data["PA"]),
                        "ab": safe_int_conversion(player_data["AB"]),
                        "r": safe_int_conversion(player_data["R"]),
                        "h": safe_int_conversion(player_data["H"]),
                        "doubles": safe_int_conversion(player_data["2B"]),
                        "triples": safe_int_conversion(player_data["3B"]),
                        "hr": safe_int_conversion(player_data["HR"]),
                        "rbi": safe_int_conversion(player_data["RBI"]),
                        "sb": safe_int_conversion(player_data["SB"]),
                        "cs": safe_int_conversion(player_data["CS"]),
                        "bb": safe_int_conversion(player_data["BB"]),
                        "so": safe_int_conversion(player_data["SO"]),
                        "ba": 0+safe_float_conversion(player_data["BA"]),
                        "obp": 0+safe_float_conversion(player_data["OBP"]),
                        "slg": 0+safe_float_conversion(player_data["SLG"]),
                        "ops": 0+safe_float_conversion(player_data["OPS"]),
                        "opSplus": safe_int_conversion(player_data["OPS+"]),
                        "rOBA": 0+existing_data["rOBA"],
                        "rbatplus": existing_data["rbatplus"],
                        "tb": safe_int_conversion(player_data["TB"]),
                        "gidp": safe_int_conversion(player_data["GDP"]),
                        "hbp": safe_int_conversion(player_data["HBP"]),
                        "sh": safe_int_conversion(player_data["SH"]),
                        "sf": safe_int_conversion(player_data["SF"]),
                        "ibb": safe_int_conversion(player_data["IBB"]),
                        "pos": player_data["Pos"],
                        "date": current_datetime
                    }

                    # Perform the PUT request
                    put_response = requests.put(api_urlPUT, json=put_payload, verify=False)  # Disable SSL verification
                    if put_response.status_code == 200:
                        print(f"Successfully updated {player_data['Name']} ({bbrefID})")
                    else:
                        print(f"Failed to update {player_data['Name']} ({bbrefID}) post response code:{put_response.status_code}")

                elif response.status_code == 404:
                    # Player does not exist, perform a POST request
                    post_payload = {
                        "BbrefId": bbrefID,
                        "Name": player_data["Name"].replace("#", ""),  # Remove special character
                        "Age": int(player_data["Age"]),
                        "Year": 2024,
                        "Team": team_abbr,
                        "Lg": get_league_by_team(team_abbr),
                        "WAR": 0.0,  
                        "G": int(player_data["G"]),
                        "PA": int(player_data["PA"]),
                        "AB": int(player_data["AB"]),
                        "R": int(player_data["R"]),
                        "H": int(player_data["H"]),
                        "Doubles": int(player_data["2B"]),
                        "Triples": int(player_data["3B"]),
                        "HR": int(player_data["HR"]),
                        "RBI": int(player_data["RBI"]),
                        "SB": int(player_data["SB"]),
                        "CS": int(player_data["CS"]),
                        "BB": int(player_data["BB"]),
                        "SO": int(player_data["SO"]),
                        "BA": 0+float(player_data["BA"]),
                        "OBP": 0+float(player_data["OBP"]),
                        "SLG": 0+float(player_data["SLG"]),
                        "OPS": 0+float(player_data["OPS"]),
                        "OPSplus": max(int(player_data["OPS+"]), 0),  # Ensure no negative values
                        "rOBA": 0.0,
                        "Rbatplus": 0,
                        "TB": int(player_data["TB"]),
                        "GIDP": int(player_data["GDP"]),
                        "HBP": int(player_data["HBP"]),
                        "SH": int(player_data["SH"]),
                        "SF": int(player_data["SF"]),
                        "IBB": int(player_data["IBB"]),
                        "Pos": player_data["Pos"],
                        "Date": datetime.now().replace(microsecond=0).isoformat()
                    }

                    # Perform the POST request
                    post_response = requests.post(api_urlPOST, json=post_payload, verify=False)  # Disable SSL verification
                    if post_response.status_code == 201:
                        print(f"Successfully created {player_data['Name']} ({bbrefID})")
                    else:
                        print(f"Failed to create {player_data['Name']} ({bbrefID}) post response code:{post_response.status_code}")
                        print(post_payload)
                else:
                    print(f"Error checking {player_data['Name']} ({bbrefID}): {response.status_code}")

# Example usage:
# Get today's date in the format 'YY-MM-DD'
today_str = datetime.now().strftime('%y-%m-%d')
teams_with_games = get_game_teams(today_str)

# Scrape and update stats only for teams with games today
for team in teams_with_games:
    get_team_batting_data(team)
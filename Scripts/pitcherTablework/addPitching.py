import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

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
    "CIN": "NL", "CLE": "AL", "COL": "NL", "DET": "AL", "HOU": "AL", "KCR": "AL",
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

def send_pitcher_data_to_db(pitcher_data, bbrefID):
    try:
        # API endpoint to check if the player exists
        api_urlGET = f"https://localhost:44346/api/Pitchers/{bbrefID}"
        api_urlPUT = f"https://localhost:44346/api/Pitchers/{bbrefID}"
        api_urlPOST = f"https://localhost:44346/api/Pitchers"

        # Check if the pitcher exists
        response = requests.get(api_urlGET, verify=False)
        
        if response.status_code == 200:
            # Pitcher exists, so update the record
            put_response = requests.put(api_urlPUT, json=pitcher_data, verify=False)
            if put_response.status_code == 200:
                print(f"Successfully updated pitcher {bbrefID}.")
            else:
                print(f"Failed to update pitcher {bbrefID}. Response: {put_response.status_code} - {put_response.text}")
        elif response.status_code == 404:
            # Pitcher does not exist, so create a new record
            post_response = requests.post(api_urlPOST, json=pitcher_data, verify=False)
            if post_response.status_code == 201:
                print(f"Successfully created pitcher {bbrefID}.")
            else:
                print(f"Failed to create pitcher {bbrefID}. Response: {post_response.status_code} - {post_response.text}")
        else:
            print(f"Error checking existence of pitcher {bbrefID}. Response: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error sending pitcher data to the database: {e}")

def get_team_pitching_data(team_name):
    team_abbr = team_abbreviations.get(team_name, None)
    if not team_abbr:
        print(f"Team {team_name} not found.")
        return
    
    url = f"https://www.baseball-reference.com/teams/{team_abbr}/2024.shtml"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve data for {team_name}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', id='team_pitching')
    
    if not table:
        print("Team Pitching table not found.")
        return
    
    rows = table.find_all('tr')
    
    for row in rows:
        try:
            # Extract and clean up player name and determine Throws
            name_cell = row.find('td', {'data-stat': 'player'})
            if name_cell and name_cell.find('a'):
                player_name = name_cell.getText().strip()
                if '*' in player_name:
                    throws = 'LHP'
                else:
                    throws = 'RHP'
                
                player_name = re.sub(r'\s*\(.*\)$', '', player_name).replace('*', '').strip()
                
                # Extract bbrefID from the href attribute
                href = name_cell.find('a')['href']
                bbrefID = href.split('/')[-1].replace('.shtml', '')
            else:
                bbrefID = None
                throws = 'RHP'  # Default to RHP if no name is found
            
            # Skip rows without a bbrefID
            if not bbrefID:
                continue

            # Extract win-loss data
            wins = row.find(attrs={'data-stat': 'W'}).text
            losses = row.find(attrs={'data-stat': 'L'}).text
            win_loss_record = f"{wins}-{losses}"

            # Create the payload object
            pitcher_data = {
                "bbrefID": bbrefID,
                "Year": 2024,
                "Age": int(row.find(attrs={'data-stat': 'age'}).text) if row.find(attrs={'data-stat': 'age'}) else None,
                "Team": team_abbr,
                "Lg": get_league_by_team(team_abbr),
                "WL": win_loss_record,
                "WLPercentage": float(row.find(attrs={'data-stat': 'win_loss_perc'}).text or 0) if row.find(attrs={'data-stat': 'win_loss_perc'}) else 0,
                "ERA": float(row.find(attrs={'data-stat': 'earned_run_avg'}).text or 0) if row.find(attrs={'data-stat': 'earned_run_avg'}) else 0,
                "G": int(row.find(attrs={'data-stat': 'G'}).text or 0) if row.find(attrs={'data-stat': 'G'}) else 0,
                "GS": int(row.find(attrs={'data-stat': 'GS'}).text or 0) if row.find(attrs={'data-stat': 'GS'}) else 0,
                "GF": int(row.find(attrs={'data-stat': 'GF'}).text or 0) if row.find(attrs={'data-stat': 'GF'}) else 0,
                "CG": int(row.find(attrs={'data-stat': 'CG'}).text or 0) if row.find(attrs={'data-stat': 'CG'}) else 0,
                "SHO": int(row.find(attrs={'data-stat': 'SHO'}).text or 0) if row.find(attrs={'data-stat': 'SHO'}) else 0,
                "SV": int(row.find(attrs={'data-stat': 'SV'}).text or 0) if row.find(attrs={'data-stat': 'SV'}) else 0,
                "IP": float(row.find(attrs={'data-stat': 'IP'}).text or 0) if row.find(attrs={'data-stat': 'IP'}) else 0,
                "H": int(row.find(attrs={'data-stat': 'H'}).text or 0) if row.find(attrs={'data-stat': 'H'}) else 0,
                "R": int(row.find(attrs={'data-stat': 'R'}).text or 0) if row.find(attrs={'data-stat': 'R'}) else 0,
                "ER": int(row.find(attrs={'data-stat': 'ER'}).text or 0) if row.find(attrs={'data-stat': 'ER'}) else 0,
                "HR": int(row.find(attrs={'data-stat': 'HR'}).text or 0) if row.find(attrs={'data-stat': 'HR'}) else 0,
                "BB": int(row.find(attrs={'data-stat': 'BB'}).text or 0) if row.find(attrs={'data-stat': 'BB'}) else 0,
                "IBB": int(row.find(attrs={'data-stat': 'IBB'}).text or 0) if row.find(attrs={'data-stat': 'IBB'}) else 0,
                "SO": int(row.find(attrs={'data-stat': 'SO'}).text or 0) if row.find(attrs={'data-stat': 'SO'}) else 0,
                "HBP": int(row.find(attrs={'data-stat': 'HBP'}).text or 0) if row.find(attrs={'data-stat': 'HBP'}) else 0,
                "BK": int(row.find(attrs={'data-stat': 'BK'}).text or 0) if row.find(attrs={'data-stat': 'BK'}) else 0,
                "WP": int(row.find(attrs={'data-stat': 'WP'}).text or 0) if row.find(attrs={'data-stat': 'WP'}) else 0,
                "BF": int(row.find(attrs={'data-stat': 'batters_faced'}).text or 0) if row.find(attrs={'data-stat': 'batters_faced'}) else 0,
                "ERAPlus": int(row.find(attrs={'data-stat': 'earned_run_avg_plus'}).text or 0) if row.find(attrs={'data-stat': 'earned_run_avg_plus'}) else 0,
                "FIP": float(row.find(attrs={'data-stat': 'fip'}).text or 0) if row.find(attrs={'data-stat': 'fip'}) else 0,
                "WHIP": float(row.find(attrs={'data-stat': 'whip'}).text or 0) if row.find(attrs={'data-stat': 'whip'}) else 0,
                "H9": float(row.find(attrs={'data-stat': 'hits_per_nine'}).text or 0) if row.find(attrs={'data-stat': 'hits_per_nine'}) else 0,
                "HR9": float(row.find(attrs={'data-stat': 'home_runs_per_nine'}).text or 0) if row.find(attrs={'data-stat': 'home_runs_per_nine'}) else 0,
                "BB9": float(row.find(attrs={'data-stat': 'bases_on_balls_per_nine'}).text or 0) if row.find(attrs={'data-stat': 'bases_on_balls_per_nine'}) else 0,
                "SO9": float(row.find(attrs={'data-stat': 'strikeouts_per_nine'}).text or 0) if row.find(attrs={'data-stat': 'strikeouts_per_nine'}) else 0,
                "SOW": float(row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}).text or 0) if row.find(attrs={'data-stat': 'strikeouts_per_base_on_balls'}) else 0,
                "Throws": throws
            }

            # Send the pitcher data to the database
            send_pitcher_data_to_db(pitcher_data, bbrefID)

        except Exception as e:
            print(f"Error processing row for {team_name}: {e}")
    
# Example usage:
for team in teams_with_games:
    get_team_pitching_data(team)

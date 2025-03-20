import requests
from bs4 import BeautifulSoup, Comment
import json
from datetime import datetime
import re
import time
import urllib3

# Suppress only the insecure request warning for localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    "CIN": "NL", "CLE": "AL", "COL": "NL", "DET": "AL", "HOU": "AL", "KCR": "AL",
    "LAA": "AL", "LAD": "NL", "MIA": "NL", "MIL": "NL", "MIN": "AL", "NYM": "NL",
    "NYY": "AL", "OAK": "AL", "PHI": "NL", "PIT": "NL", "SDP": "NL", "SEA": "AL",
    "SFG": "NL", "STL": "NL", "TBR": "AL", "TEX": "AL", "TOR": "AL", "WSN": "NL"
}

# Safe conversion functions
def safe_int_conversion(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float_conversion(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_string_conversion(value, default=''):
    try:
        return str(value)
    except (ValueError, TypeError):
        return default

def get_league_by_team(team_abbr):
    return teamLg.get(team_abbr, "Unknown")

def get_game_teams(date_str):
    date_str = '24-09-28'#this is a passthrough....
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

def debug_print_all_tables(soup, team_name):
    print(f"Debugging all tables for {team_name}:")
    tables = soup.find_all('table')
    if not tables:
        print(f"No tables found for {team_name}.")
        return
    
    for i, table in enumerate(tables):
        table_id = table.get('id', 'No ID')
        table_classes = table.get('class', 'No Class')
        caption = table.find('caption')
        caption_text = caption.get_text(strip=True) if caption else 'No Caption'
        
        print(f"Table {i + 1}:")
        print(f"  ID: {table_id}")
        print(f"  Classes: {table_classes}")
        print(f"  Caption: {caption_text}")
        print('-' * 40)

def debug_team_divs(soup):
    # Find the parent divs for batting and pitching tables
    batting_div = soup.find('div', id='all_players_standard_batting')
    pitching_div = soup.find('div', id='all_players_standard_pitching')

    # Check if the batting div is found
    if batting_div:
        print("Batting div found.")
        # Find the table inside the batting div
        batting_table = batting_div.find('table')
        if batting_table:
            print("Batting table found in batting div.")
            print(f"Table ID: {batting_table.get('id')}")
        else:
            print("No table found in batting div.")
    else:
        print("Batting div not found.")

    # Check if the pitching div is found
    if pitching_div:
        print("Pitching div found.")
        print("Printing full HTML content of the pitching div for debugging:")
        print(pitching_div.prettify())  # Print the full HTML of the pitching div
        
        # Attempt to find the direct child div with the table
        pitching_table_div = pitching_div.find('div', id='div_players_standard_pitching')
        if pitching_table_div:
            print("Pitching table div found.")
            # Find the table inside this div
            pitching_table = pitching_table_div.find('table')
            if pitching_table:
                print("Pitching table found in pitching table div.")
                print(f"Table ID: {pitching_table.get('id')}")
            else:
                print("No table found in pitching table div.")
        else:
            print("Pitching table div not found.")
    else:
        print("Pitching div not found.")


def get_team_pitching_data(team_name, soup):
    team_abbr = team_abbreviations.get(team_name, None)
    if not team_abbr:
        print(f"Team {team_name} not found.")
        return

# we might have to move all out pitching scraping into this comment section.... might only be bc 2024 is finalized though
    # Locate the pitching div
    # pitching_div = soup.find('div', id='all_players_standard_pitching')
    # if not pitching_div:
    #     print(f"Pitching div not found for {team_name}.")
    #     return

    # # Extract commented-out HTML within the pitching div
    # comments = pitching_div.find_all(string=lambda text: isinstance(text, Comment))
    # if not comments:
    #     print(f"No commented-out HTML found in the pitching div for {team_name}.")
    #     return

    # # Parse the first comment containing the table
    # for comment in comments:
    #     comment_soup = BeautifulSoup(comment, 'html.parser')
    #     pitching_table = comment_soup.find('table', id='players_standard_pitching')
    #     if pitching_table:
    #         print(f"Pitching table found for {team_name}. Table ID: {pitching_table.get('id')}")
    #         # Process the table rows as needed
    #         rows = pitching_table.find_all('tr')
    #         for row in rows:
    #             try:
    #                 # Add your existing row processing logic here
    #                 pass
    #             except Exception as e:
    #                 print(f"Error processing row for {team_name}: {e}")
    #         return


    #table = soup.find('table', id='team_pitching')#this was correct for reg season
    table = soup.find('table', id='players_standard_pitching')#something changed now season numbers are finalized
    
    if not table:
        print("Team Pitching table not found via divs."+ team_name)
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
                "Year": 2025,
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
                "Throws": throws,
                "DateModified": current_datetime
            }

            # Send the pitcher data to the database
            send_pitcher_data_to_db(pitcher_data, bbrefID)

        except Exception as e:
            print(f"Error processing row for {team_name}: {e}")

def get_team_batting_data(team_name, soup):
    team_abbr = team_abbreviations.get(team_name, None)
    if not team_abbr:
        print(f"Team {team_name} not found.")
        return
    
    table = soup.find('table', id='team_batting')#this was correct for regular season....
    #table = soup.find('table', id='players_standard_batting')#something changed now season numbers are finalized
    
    if not table:
        print("Team Batting table not found."+ team_name)
        return
    
    rows = table.find_all('tr')
    
    headers = [
        "Pos", "Name", "Age", "G", "PA", "AB", "R", "H", "2B", "3B", "HR", "RBI", "SB", "CS", 
        "BB", "SO", "BA", "OBP", "SLG", "OPS", "OPS+", "TB", "GDP", "HBP", "SH", "SF", "IBB", "bbrefID"
    ]
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 0:  # Ensure row has data
            row_data = [cell.getText().strip() for cell in cells]
            
            # Extract and clean up player name
            name_cell = row.find('td', {'data-stat': 'player'})
            if name_cell and name_cell.find('a'):
                player_name = name_cell.getText().strip()
                
                # Determine Bats value based on name suffix
                if '*' in player_name:
                    bats = 'LH'
                elif '#' in player_name:
                    bats = 'S'
                else:
                    bats = 'RH'
                
                # Remove trailing (10-day IL) or other parenthetical expressions
                player_name = re.sub(r'\s*\(.*\)$', '', player_name).replace('*', '').replace('#', '').strip()

                # Extract bbrefID from the href attribute in the Name column
                href = name_cell.find('a')['href']
                bbrefID = href.split('/')[-1].replace('.shtml', '')  # Extract bbrefID
            else:
                bbrefID = None
            
            # Skip rows where Pos is 'P' (pitchers) or bbrefID is None
            if row_data[0].strip() != 'P' and bbrefID is not None:
                # Create a temporary dictionary with player data
                player_data = dict(zip(headers, row_data + [bbrefID]))
                player_data['Name'] = player_name  # Update player name without special characters
                player_data['Bats'] = bats  # Add Bats to the player data
                player_data['BA'] = safe_float_conversion(player_data.get('BA', ''), 0)
                player_data['OBP'] = safe_float_conversion(player_data.get('OBP', ''), 0)
                player_data['SLG'] = safe_float_conversion(player_data.get('SLG', ''), 0)
                player_data['OPS'] = safe_float_conversion(player_data.get('OPS', ''), 0)
                player_data['OPS+'] = safe_int_conversion(player_data.get('OPS+', ''), 0)

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
                        "year": 2025,
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
                        "date": current_datetime,
                        "bats": bats  # Include Bats in the payload
                    }

                    # Perform the PUT request
                    put_response = requests.put(api_urlPUT, json=put_payload, verify=False)  # Disable SSL verification
                    if put_response.status_code == 200:
                        print(f"Successfully updated {player_data['Name']} ({bbrefID})")
                    if put_response.status_code == 204:
                        print(f"Successfully Partial update for {player_data['Name']} ({bbrefID})")
                    else:
                        print(f"Failed to update {player_data['Name']} ({bbrefID}) post response code:{put_response.status_code}")

                elif response.status_code == 404:
                    # Player does not exist, perform a POST request
                    post_payload = {
                        "BbrefId": bbrefID,
                        "Name": player_data["Name"].replace("#", ""),  # Remove special character
                        "Age": int(player_data["Age"]),
                        "Year": 2025,
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
                        "Date": datetime.now().replace(microsecond=0).isoformat(),
                        "Bats": bats  # Include Bats in the payload
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

def process_team_data(team_name):
    # Get the abbreviation for the team
    team_abbr = team_abbreviations.get(team_name, None)
    if not team_abbr:
        print(f"Team {team_name} not found.")
        return
    
    # Create the URL
    url = f"https://www.baseball-reference.com/teams/{team_abbr}/2025.shtml"
    time.sleep(2)
    # Fetch the page
    response = requests.get(url)
    response.encoding = 'utf-8'

    if response.status_code != 200:
        print(f"Failed to retrieve data for {team_name}")
        return
    else:
        print(f"fetched {url}")
    
    # Parse the page
    soup = BeautifulSoup(response.text, 'html.parser',from_encoding='utf-8') #need encoding to handle letters with spanish accents
    
    # Get both batting and pitching data
    get_team_batting_data(team_name, soup)
    get_team_pitching_data(team_name, soup)

# Add a passthrough flag
process_all_teams = False  # Set to True to process all teams, False to process only teams with games

# Example usage:
if process_all_teams:
    for team in team_abbreviations.keys():  # Process all teams from the abbreviations dictionary
        process_team_data(team)
else:
    for team in teams_with_games:  # Process only teams with games
        process_team_data(team)


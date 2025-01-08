import requests
import re
from bs4 import BeautifulSoup, Comment
import json
from datetime import datetime


# Define the URL for the box score page
BOX_SCORE_URL = "https://www.baseball-reference.com/boxes/LAN/LAN202408280.shtml"
# Define the URLs for your API endpoints (commented out for testing)
# GAME_API_URL = "https://localhost:44346/api/ML_Games"
# LINEUP_API_URL = "https://localhost:44346/api/ML_Lineups"
# PITCHING_API_URL = "https://localhost:44346/api/ML_PitchingStats"
# BOXSCORE_API_URL = "https://localhost:44346/api/ML_BoxScores"
# PLAYER_API_URL = "https://localhost:44346/api/ML_Players"
# TEAM_API_URL = "https://localhost:44346/api/ML_Teams"
BALLPARK_API_URL = "https://localhost:44346/api/ParkFactors"
# WEATHER_API_URL = "https://localhost:44346/api/ML_Weather"


teams = {
#starting point of team Table mapping
    1: {"TeamName": "Arizona Diamondbacks", "Abbreviation": "ARI"},
    2: {"TeamName": "Atlanta Braves", "Abbreviation": "ATL"},
    3: {"TeamName": "Baltimore Orioles", "Abbreviation": "BAL"},
    4: {"TeamName": "Boston Red Sox", "Abbreviation": "BOS"},
    5: {"TeamName": "Chicago White Sox", "Abbreviation": "CHW"},
    6: {"TeamName": "Chicago Cubs", "Abbreviation": "CHC"},
    7: {"TeamName": "Cincinnati Reds", "Abbreviation": "CIN"},
    8: {"TeamName": "Cleveland Guardians", "Abbreviation": "CLE"},
    9: {"TeamName": "Colorado Rockies", "Abbreviation": "COL"},
    10: {"TeamName": "Detroit Tigers", "Abbreviation": "DET"},
    11: {"TeamName": "Houston Astros", "Abbreviation": "HOU"},
    12: {"TeamName": "Kansas City Royals", "Abbreviation": "KCR"},
    13: {"TeamName": "Los Angeles Angels", "Abbreviation": "LAA"},
    14: {"TeamName": "Los Angeles Dodgers", "Abbreviation": "LAD"},
    15: {"TeamName": "Miami Marlins", "Abbreviation": "MIA"},
    16: {"TeamName": "Milwaukee Brewers", "Abbreviation": "MIL"},
    17: {"TeamName": "Minnesota Twins", "Abbreviation": "MIN"},
    18: {"TeamName": "New York Yankees", "Abbreviation": "NYY"},
    19: {"TeamName": "New York Mets", "Abbreviation": "NYM"},
    20: {"TeamName": "Oakland Athletics", "Abbreviation": "OAK"},
    21: {"TeamName": "Philadelphia Phillies", "Abbreviation": "PHI"},
    22: {"TeamName": "Pittsburgh Pirates", "Abbreviation": "PIT"},
    23: {"TeamName": "San Diego Padres", "Abbreviation": "SDP"},
    24: {"TeamName": "San Francisco Giants", "Abbreviation": "SFG"},
    25: {"TeamName": "Seattle Mariners", "Abbreviation": "SEA"},
    26: {"TeamName": "St. Louis Cardinals", "Abbreviation": "STL"},
    27: {"TeamName": "Tampa Bay Rays", "Abbreviation": "TBR"},
    28: {"TeamName": "Texas Rangers", "Abbreviation": "TEX"},
    29: {"TeamName": "Toronto Blue Jays", "Abbreviation": "TOR"},
    30: {"TeamName": "Washington Nationals", "Abbreviation": "WSN"}
}
def update_cumulative_stats(soup, lineup, team_type):
    # Select the appropriate footer section based on team type
    footer_id = f'tfooter_{team_type.capitalize()}'
    footer_section = soup.find('div', id=footer_id)

    if not footer_section:
        print(f"No footer section found for team {team_type}")
        return

    # Update HR
    hr_section = footer_section.find('div', id=f'HR{team_type}')
    if hr_section:
        hr_text = hr_section.get_text()
        for player in lineup:
            if player['player'] in hr_text:
                # Extract the number of HRs from the text
                match = re.search(rf"{player['player']}.*?\((\d+)", hr_text)
                if match:
                    player['cumulative_stats']['HR'] = int(match.group(1))

    # Update RBI
    rbi_section = footer_section.find('div', id=f'RBI{team_type}')
    if rbi_section:
        rbi_text = rbi_section.get_text()
        for player in lineup:
            if player['player'] in rbi_text:
                # Extract the number of RBIs from the text
                match = re.search(rf"{player['player']}.*?\((\d+)", rbi_text)
                if match:
                    player['cumulative_stats']['RBI'] = int(match.group(1))

    # Update SB
    sb_section = footer_section.find('div', id=f'SB{team_type}')
    if sb_section:
        sb_text = sb_section.get_text()
        for player in lineup:
            if player['player'] in sb_text:
                # Extract the number of SBs from the text
                match = re.search(rf"{player['player']}.*?\((\d+)", sb_text)
                if match:
                    player['cumulative_stats']['SB'] = int(match.group(1))

def extract_pitching_stats(soup, game_id):
    pitching_stats = []
    teams = [('Home', 1), ('Away', 2)]  # Replace with actual team IDs
    
    for team_name, team_id in teams:
        pitching_table = soup.find('table', id=f'{team_name.lower()}-pitching')
        if not pitching_table:
            print(f"Pitching table for {team_name} not found.")
            continue
        
        for row in pitching_table.find_all('tr', class_=lambda x: x != 'thead'):
            player_cell = row.find('th', {'data-stat': 'player'})
            player_name = player_cell.get_text(strip=True)
            bbrefid = player_cell['data-append-csv']
            
            # Game stats mapping
            game_stats = {
                'IP': 0, 'H': 0, 'R': 0, 'ER': 0, 'BB': 0, 'SO': 0,
                'HR': 0, 'BF': 0, 'Pit': 0, 'Str': 0, 'Ctct': 0, 'StS': 0,
                'StL': 0, 'GB': 0, 'FB': 0, 'LD': 0, 'Unk': 0, 'GSc': 0,
                'IR': 0, 'IS': 0, 'WPA': 0, 'aLI': 0, 'cWPA': 0, 'acLI': 0,
                'RE24': 0
            }
            
            # Cumulative stats mapping
            cumulative_stats = {
                'ERA': 0.0,
                'W-L': '0-0'
            }

            # Mapping to the correct td elements
            game_stats_mapping = {
                'IP': 0, 'H': 1, 'R': 2, 'ER': 3, 'BB': 4, 'SO': 5,
                'HR': 6, 'ERA': 7, 'BF': 8, 'Pit': 9, 'Str': 10, 'Ctct': 11, 
                'StS': 12, 'StL': 13, 'GB': 14, 'FB': 15, 'LD': 16, 'Unk': 17,
                'GSc': 18, 'IR': 19, 'IS': 20, 'WPA': 21, 'aLI': 22, 'cWPA': 23,
                'acLI': 24, 'RE24': 25
            }

            tds = row.find_all('td')
            for stat, idx in game_stats_mapping.items():
                try:
                    if stat == 'ERA':
                        cumulative_stats['ERA'] = float(tds[idx].get_text(strip=True))
                    else:
                        game_stats[stat] = float(tds[idx].get_text(strip=True))
                except (ValueError, IndexError):
                    continue
            
            # Update W-L record from the player's name column
            win_loss_match = re.search(r'\((\d+-\d+)\)', player_name)
            if win_loss_match:
                cumulative_stats['W-L'] = win_loss_match.group(1)
            
            pitching_data = {
                'GameID': game_id,
                'PlayerID': bbrefid,
                'TeamID': team_id,
                'GameStats': game_stats,
                'CumulativeStats': cumulative_stats
            }
            pitching_stats.append(pitching_data)
    
    return pitching_stats


def parse_stat_entry(entry, stat_type):
    """
    Parse the player name and stat count from an entry string.
    Example entry: 'Shohei Ohtani (42, off Corbin Burnes, 1st inn, 0 on, 0 outs to Deep RF)'
    """
    name = entry.split('(')[0].strip().replace(u'\xa0', u' ')
    stat_count = int(re.search(r'\d+', entry.split('(')[1]).group())
    return name, stat_count

def update_player_stat(lineups, player_name, stat_key, stat_value):
    """
    Update the player's cumulative stats with the given stat.
    """
    for player in lineups:
        if player['player'].replace(u'\xa0', u' ') == player_name:
            player['cumulative_stats'][stat_key] = stat_value
            break

def convert_date_format(raw_date):
    # Convert the date from "August 28, 2024" to "08-28-2024"
    date_obj = datetime.strptime(raw_date, "%B %d, %Y")
    formatted_date = date_obj.strftime("%m-%d-%Y")
    return formatted_date

def get_ballpark_data():
    # Send a GET request to the ParkFactors API
    response = requests.get(BALLPARK_API_URL, verify=False)
    
    if response.status_code == 200:
        # Convert the response to JSON format
        ballparks = response.json()
        
        # Create a dictionary to store ballpark data with the ballpark ID as the key
        ballpark_dict = {}
        
        for ballpark in ballparks:
            ballpark_dict[ballpark['id']] = ballpark
        
        return ballpark_dict
    else:
        print(f"Failed to retrieve ballpark data. Status code: {response.status_code}")
        return None

        
def scrape_box_score(url, ballpark_data):
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to retrieve box score data. Status code: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    game_info = extract_game_info(soup, ballpark_data)
    print("Game Info:", game_info)
    
    lineups = extract_lineups(soup, game_info['BallparkID'], game_info['HomeTeamName'], game_info['AwayTeamName'])
    
    pitching_stats = extract_pitching_stats(soup, game_info['BallparkID'])
    if pitching_stats:
        print("Pitching Stats:", pitching_stats)
    
    box_scores = extract_box_scores(soup, game_info['BallparkID'])
    if box_scores:
        print("Box Scores:", box_scores)
    
    weather_info = extract_weather_info(soup, ballpark_data, game_info['BallparkID'])
    if weather_info:
        print("Weather Info:", weather_info)



def extract_game_info(soup, ballpark_data):
    content_div = soup.find('div', id='content')
    header = content_div.find('h1').get_text(strip=True)
    
    parts = header.split(' Box Score: ')
    teams_part = parts[0]
    away_team_name, home_team_name = teams_part.split(' vs ')
    # Extract and convert the game date
    raw_date = parts[1]
    game_date = convert_date_format(raw_date)
    
    scorebox = soup.find('div', class_='scorebox')
    home_team_score = int(scorebox.find_all('div', class_='score')[1].get_text(strip=True))
    away_team_score = int(scorebox.find_all('div', class_='score')[0].get_text(strip=True))
    result = 'HomeWin' if home_team_score > away_team_score else 'AwayWin'
    
    linescore_table = soup.find('table', id='linescore')
    extra_innings = 1 if linescore_table and len(linescore_table.find_all('th')) > 9 else 0
    
    # Extract team records
    team_records = scorebox.find_all('div', text=re.compile(r'\d+-\d+'))
    away_team_record = team_records[0].get_text(strip=True)
    home_team_record = team_records[1].get_text(strip=True)
    
    away_team_wins, away_team_losses = map(int, away_team_record.split('-'))
    home_team_wins, home_team_losses = map(int, home_team_record.split('-'))
    
    away_team_ties = 0
    home_team_ties = 0

    ballpark_id = None
    for park_id, park_info in ballpark_data.items():
        if park_info['team'].lower() in home_team_name.lower():
            ballpark_id = park_id
            break
    
    if ballpark_id is None:
        print(f"Warning: Ballpark ID not found for home team {home_team_name}.")
        ballpark_id = -1

    weather_id = 1
    home_team_id = 1
    away_team_id = 2
    
    # Extract start time
    scorebox_meta = soup.find('div', class_='scorebox_meta')
    start_time = None
    if scorebox_meta:
        start_time_match = re.search(r'Start Time: (\d{1,2}:\d{2} [ap]\.m\.)', scorebox_meta.get_text(strip=True))
        if start_time_match:
            start_time = start_time_match.group(1)

    game_info = {
        'Date': game_date,
        'HomeTeamScore': home_team_score,
        'AwayTeamScore': away_team_score,
        'Result': result,
        'ExtraInnings': extra_innings,
        'BallparkID': ballpark_id,
        'WeatherID': weather_id,
        'HomeTeamID': home_team_id,
        'AwayTeamID': away_team_id,
        'HomeTeamName': home_team_name,
        'AwayTeamName': away_team_name,
        'HomeTeamWins': home_team_wins,
        'HomeTeamLosses': home_team_losses,
        'HomeTeamTies': home_team_ties,
        'AwayTeamWins': away_team_wins,
        'AwayTeamLosses': away_team_losses,
        'AwayTeamTies': away_team_ties,
        'StartTime': start_time
    }
    
    return game_info

def extract_lineups(soup, ballpark_id, home_team_name, away_team_name):
    # Remove spaces from team names to match the format in the comment
    home_team_key = home_team_name.replace(" ", "")
    away_team_key = away_team_name.replace(" ", "")

    # Define valid positions
    valid_positions = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH", "PH", "PR", "P"]

    # Find the comment that contains the lineup table
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    lineup_comments = []

    for comment in comments:
        if f'{home_team_key}batting' in comment or f'{away_team_key}batting' in comment:
            lineup_comments.append(comment)

    if not lineup_comments:
        print("Lineup comments not found!")
        return None

    # Initialize the lists
    home_lineups = []
    away_lineups = []
    home_substitutions = []
    away_substitutions = []
    home_pitchers = []
    away_pitchers = []


    for lineup_comment in lineup_comments:
        # Determine if this is home or away based on the comment content
        if f'{home_team_key}batting' in lineup_comment:
            current_lineups = home_lineups
            current_substitutions = home_substitutions
            current_pitchers = home_pitchers
        else:
            current_lineups = away_lineups
            current_substitutions = away_substitutions
            current_pitchers = away_pitchers

        # Parse the comment as HTML with the correct encoding
        lineup_soup = BeautifulSoup(lineup_comment, 'html.parser')

        # Find the table within the parsed comment
        lineup_table = lineup_soup.find('table')

        if lineup_table is None:
            print("Lineup table not found in comment!")
            continue

        order = 1  # Start the order at 1
        last_substitution_position = None  # Track the last substitution position

        for row in lineup_table.find_all('tr', class_=lambda x: x != 'thead'):
            player_cell = row.find('th', {'data-stat': 'player'})
            player_text = player_cell.get_text().strip() if player_cell else ''

            # Extract the bbrefid from the link
            link_tag = player_cell.find('a', href=True)
            bbrefid = link_tag['href'].split('/')[-1].replace('.shtml', '') if link_tag else None

            # Extract player name and position
            player_name = player_text
            position = "N/A"

            # Handle positions with PH or PR as wildcards
            if "PH-" in player_text or "PR-" in player_text:
                position = player_text.split(' ')[-1]  # Get the entire PH-XX or PR-XX as the position
                player_name = player_text.replace(f" {position}", "").strip()
            else:
                # Regular position extraction
                for pos in valid_positions:
                    if player_text.endswith(f" {pos}") or f" {pos}-" in player_text:
                        position = pos
                        player_name = player_text.replace(f" {pos}", "").replace(f" {pos}-", "").strip()
                        break

            # Extract game and cumulative stats
            game_stats, cumulative_stats = extract_stats(row)

            # Handle pitchers separately
            if position == 'P':
                # Set the first pitcher as SP and the rest as RP
                if len(current_pitchers) == 0:
                    current_pitchers.append({'order': len(current_pitchers) + 1, 'player': player_name, 'position': 'SP', 'bbrefid': bbrefid})
                else:
                    current_pitchers.append({'order': len(current_pitchers) + 1, 'player': player_name, 'position': 'RP', 'bbrefid': bbrefid})
                continue

            # Handle substitutions
            if last_substitution_position:
                if position.startswith(last_substitution_position.split('-')[1]) or position.startswith('PH') or position.startswith('PR'):
                    current_substitutions.append({'order': order - 1, 'player': player_name, 'position': position, 'bbrefid': bbrefid, 'game_stats': game_stats, 'cumulative_stats': cumulative_stats})
                else:
                    current_lineups.append({'order': order, 'player': player_name, 'position': position, 'bbrefid': bbrefid, 'game_stats': game_stats, 'cumulative_stats': cumulative_stats})
                    order += 1
                last_substitution_position = None
            elif "PH" in position or "PR" in position:
                current_substitutions.append({'order': order - 1, 'player': player_name, 'position': position, 'bbrefid': bbrefid, 'game_stats': game_stats, 'cumulative_stats': cumulative_stats})
                if '-' in position:
                    last_substitution_position = position  # Track last substitution position with hyphen
                continue
            elif current_lineups and current_lineups[-1]['position'] == position:
                current_substitutions.append({'order': order - 1, 'player': player_name, 'position': position, 'bbrefid': bbrefid, 'game_stats': game_stats, 'cumulative_stats': cumulative_stats})
                continue

            # Add the player to the lineup
            if player_name.lower() != "team totals" and position != "N/A":
                current_lineups.append({'order': order, 'player': player_name, 'position': position, 'bbrefid': bbrefid, 'game_stats': game_stats, 'cumulative_stats': cumulative_stats})
                # Increment the order only for non-substitution entries
                order += 1

    # Print the six lists before returning
    print("Home Lineups:", home_lineups)
    print("Away Lineups:", away_lineups)
    print("Home Substitutions:", home_substitutions)
    print("Away Substitutions:", away_substitutions)
    print("Home Pitchers:", home_pitchers)
    print("Away Pitchers:", away_pitchers)

    return home_lineups, away_lineups, home_substitutions, away_substitutions, home_pitchers, away_pitchers


def extract_stats(row):
    """ Extract game and cumulative stats from a player's row. """
    game_stats = {
        'AB': 0, 'R': 0, 'H': 0, 'RBI': 0, 'BB': 0, 'SO': 0, 'PA': 0, 'Pit': 0, 'Str': 0,
        'WPA': 0, 'ALI': 0, 'WPA+': 0, 'WPA-A': 0, 'cWPA': 0, 'acLI': 0, 'RE24': 0,
        'PO': 0, 'A': 0, '2B': 0, '3B': 0, 'HR': 0, 'SB': 0, 'CS': 0, 'SF': 0, 'HBP': 0, 'E': 0
    }
    cumulative_stats = {
        'BA': 0.000, 'OBP': 0.000, 'SLG': 0.000, 'OPS': 0.000
    }

    # Extract the td elements
    tds = row.find_all('td')

    # Mapping for game stats to the correct column indices
    stats_mapping = {
        'AB': 0, 'R': 1, 'H': 2, 'RBI': 3, 'BB': 4, 'SO': 5, 'PA': 6,
        'Pit': 11, 'Str': 12, 'WPA': 13, 'ALI': 14, 'WPA+': 15, 'WPA-A': 16,
        'cWPA': 17, 'acLI': 18, 'RE24': 19, 'PO': 20, 'A': 21
    }

    for stat, idx in stats_mapping.items():
        try:
            if stat == 'cWPA':
                # Handle cWPA separately due to the percentage sign
                cWPA_text = tds[idx].get_text().strip().replace('%', '')
                game_stats['cWPA'] = float(cWPA_text) / 100  # Convert percentage to a decimal
            else:
                game_stats[stat] = float(tds[idx].get_text().strip())
        except (ValueError, IndexError):
            game_stats[stat] = 0  # Default to 0 if conversion fails or index is out of range

    # Calculate AB based on PA - BB - HBP (this might be a different calculation)
    game_stats['AB'] = game_stats['PA'] - game_stats['BB'] - game_stats['HBP']

    # Extract the details column and parse extra stats
    if len(tds) > 0:
        details_text = tds[-1].get_text().strip()
        # Check for specific statistics in the details text
        if '2B' in details_text:
            game_stats['2B'] += 1
        if '3B' in details_text:
            game_stats['3B'] += 1
        if 'HR' in details_text:
            game_stats['HR'] += 1
        if 'SB' in details_text:
            match = re.search(r'(\d+)·SB', details_text)
            if match:
                game_stats['SB'] += int(match.group(1))
            else:
                game_stats['SB'] += 1
        if 'CS' in details_text:
            game_stats['CS'] += 1
        if 'SF' in details_text:
            game_stats['SF'] += 1
        if 'HBP' in details_text:
            game_stats['HBP'] += 1

    # Extract cumulative stats if they exist
    if len(tds) >= 11:  # Ensure we have enough tds for cumulative stats
        try:
            cumulative_stats['BA'] = float(tds[7].get_text().strip())
            cumulative_stats['OBP'] = float(tds[8].get_text().strip())
            cumulative_stats['SLG'] = float(tds[9].get_text().strip())
            cumulative_stats['OPS'] = float(tds[10].get_text().strip())
        except (ValueError, IndexError):
            pass  # If parsing fails, leave as default values

    return game_stats, cumulative_stats



def extract_player(row):
    player_name = row.find('th', {'data-stat': 'player'}).get_text(strip=True)
    position = row.find('td', {'data-stat': 'pos'}).get_text(strip=True)
    
    player_data = {
        'PlayerName': player_name,
        'Position': position,
        # Include any additional stats you might want to track
    }
    
    return player_data



def extract_box_scores(soup, game_id):
    box_scores = []
    teams = [('Home', 1), ('Away', 2)]  # Replace with actual team IDs
    
    for team_name, team_id in teams:
        batting_table = soup.find('table', id=f'{team_name.lower()}-batting')
        if not batting_table:
            print(f"Batting table for {team_name} not found.")
            continue
        
        for row in batting_table.find_all('tr', class_=lambda x: x != 'thead'):
            player_name = row.find('th', {'data-stat': 'player'}).get_text(strip=True)
            
            player_id = get_player_id(player_name, team_id)
            
            box_score_data = {
                'GameID': game_id,
                'PlayerID': player_id,
                'EventType': 'Hit',  # Add logic to determine actual event type
                'Outcome': json.dumps({'detail': 'success'}),  # Replace with actual outcome data
                'Inning': 1,  # Replace with actual inning data
                'PitchCount': 3,  # Replace with actual pitch count data
                'ScoreBeforeEvent': 0,  # Replace with actual score before event
                'ScoreAfterEvent': 1   # Replace with actual score after event
            }
            box_scores.append(box_score_data)
    
    return box_scores


def extract_weather_info(soup, ballpark_data, ballpark_id):
    content_div = soup.find('div', id='content')
    all_divs = content_div.find_all('div', id=re.compile('all'))

    # Print all div IDs found within the content div
#    for i, div in enumerate(all_divs):
#        print(f"Div {i} ID: {div.get('id')}")
    
    weather_div = all_divs[5].find(string=lambda text: isinstance(text, Comment))
    
    if weather_div:
        weather_text = weather_div.extract().strip()
        
        temp_match = re.search(r'Start Time Weather:</strong> (\d+)&deg; F', weather_text)
        temperature = int(temp_match.group(1)) if temp_match else None
        
        wind_match = re.search(r'Wind (\d+)mph (.+?),', weather_text)
        wind_speed = int(wind_match.group(1)) if wind_match else None
        wind_description = wind_match.group(2).lower() if wind_match else None
        
        field_direction = ballpark_data.get(ballpark_id, {}).get('direction', None)
        wind_direction = calculate_wind_direction(wind_description, field_direction)
        
        # Handling Precipitation
        precipitation_match = re.search(r'Precipitation: (.+?)(?=\.)', weather_text)
        if precipitation_match:
            precipitation_text = precipitation_match.group(1).strip()
            if precipitation_text.lower() == "no precipitation":
                precipitation = 0
            else:
                precipitation = 1
        else:
            precipitation = 0
        
        humidity = None
        
        weather_info = {
            'Temperature': temperature,
            'Humidity': humidity,
            'WindSpeed': wind_speed,
            'WindDirection': wind_direction,
            'Precipitation': precipitation
        }
        
        return weather_info
    else:
        print("Weather information not found.")
        return None



def calculate_wind_direction(wind_description, field_direction):
    wind_direction_map = {
        'out to rightfield': 90,
        'out to centerfield': 0,
        'out to leftfield': 270,
        'in from rightfield': 270,
        'in from centerfield': 180,
        'in from leftfield': 90,
        'left to right': 90,
        'right to left': 270,
        'straight out': 0,
        'straight in': 180
    }
    
    wind_base_direction = wind_direction_map.get(wind_description, None)
    
    if wind_base_direction is not None and field_direction is not None:
        wind_direction = (field_direction + wind_base_direction) % 360
        return wind_direction
    else:
        return None


def create_ballpark_info(ballpark_id, ballpark_data):
    # Fetch the ballpark details from the ballpark_data using the ballpark_id
    ballpark = ballpark_data.get(ballpark_id)

    if ballpark:
        # Create the ballpark_info object
        ballpark_info = {
            "ballparkID": ballpark['id'],  # Use the actual ballpark ID
            "name": ballpark['venue'],  # Name of the ballpark
            "location": ballpark['zipcode'],  # Location, assuming it’s the zipcode
            "capacity": ballpark.get('capacity', 0),  # Capacity of the ballpark, default to 0 if not provided
            "fieldDimensions": ballpark.get('fieldDimensions', ""),  # Field dimensions as a string
            "altitude": ballpark.get('altitude', 0),  # Altitude of the ballpark, default to 0 if not provided
            "parkFactors": json.dumps({
                "ParkFactorRating": ballpark.get('ParkFactorRating', None),
                "wOBACon": ballpark.get('wOBACon', None),
                "bacon": ballpark.get('bacon', None),
                "r": ballpark.get('r', None),
                "obp": ballpark.get('obp', None),
                "h": ballpark.get('h', None),
                "oneB": ballpark.get('oneB', None),
                "twoB": ballpark.get('twoB', None),
                "threeB": ballpark.get('threeB', None),
                "hr": ballpark.get('hr', None),
                "bb": ballpark.get('bb', None),
                "so": ballpark.get('so', None)
            }),  # JSON string of park factors
            "homeTeam": ballpark.get('team', ""),  # Home team of the ballpark
            "roofType": ballpark.get('roofType', ""),  # Roof type of the ballpark
            "direction": ballpark.get('direction', 0),  # Field direction, default to 0 if not provided
            "parkFactorsID": ballpark_id  # Park Factors ID, same as ballpark ID
        }
    else:
        print(f"Warning: Ballpark with ID {ballpark_id} not found.")
        ballpark_info = None

    return ballpark_info


def get_player_id(player_name, team_id):
    # Dummy player ID logic, replace with actual lookup or API call
    return 1  # Placeholder

def create_game_payload(game_info, home_team_info, away_team_info, ballpark_info, weather_info):
    game_payload = {
        "gameID": 0,  # New entry
        "date": game_info['Date'],
        "homeTeamID": 0,  # New entry
        "awayTeamID": 0,  # New entry
        "ballparkID": 0,  # New entry
        "homeTeamScore": game_info['HomeTeamScore'],
        "awayTeamScore": game_info['AwayTeamScore'],
        "weatherID": 0,  # New entry
        "result": game_info['result'],
        "extraInnings": game_info['extraInnings'],
        "homeTeam": {
            "teamID": 0,  # New entry
            "teamName": home_team_info['teamName'],
            "abbreviation": home_team_info['abbreviation'],
            "wins": home_team_info['wins'],
            "losses": home_team_info['losses'],
            "ties": home_team_info['ties']
        },
        "awayTeam": {
            "teamID": 0,  # New entry
            "teamName": away_team_info['teamName'],
            "abbreviation": away_team_info['abbreviation'],
            "wins": away_team_info['wins'],
            "losses": away_team_info['losses'],
            "ties": away_team_info['ties']
        },
        "ballpark": {
            "ballparkID": 0,  # New entry
            "name": ballpark_info['name'],
            "location": ballpark_info['location'],
            "capacity": ballpark_info['capacity'],
            "fieldDimensions": ballpark_info['fieldDimensions'],
            "altitude": ballpark_info['altitude'],
            "parkFactors": ballpark_info['parkFactors'],
            "homeTeam": ballpark_info['homeTeam'],
            "roofType": ballpark_info['roofType'],
            "direction": ballpark_info['direction'],
            "parkFactorsID": ballpark_info['parkFactorsID']
        },
        "weather": {
            "weatherID": 0,  # New entry
            "gameID": 0,  # Will be set after the game entry is created
            "temperature": weather_info['Temperature'],
            "humidity": weather_info['Humidity'],
            "windSpeed": weather_info['WindSpeed'],
            "windDirection": weather_info['WindDirection'],
            "precipitation": weather_info['Precipitation'],
            "game": "string"  # May be set later or linked after the game is created
        }
    }
    return game_payload




if __name__ == "__main__":

    ballpark_data = get_ballpark_data()
    if ballpark_data:
        print("Ballpark data successfully retrieved and stored.")
        # Pass ballpark data to the scrape function
        scrape_box_score(BOX_SCORE_URL, ballpark_data)

        #game_info = extract_game_info(soup, ballpark_data)
    else:
        print("Failed to retrieve ballpark data.")

#this all gets done in scrape_box_score as we get them
        # Example integration in the main script
        # Extract game information (which includes ballpark_id)
#        game_info = extract_game_info(soup, ballpark_data)
        # Create the ballpark_info object
 #       ballpark_info = create_ballpark_info(game_info['BallparkID'], ballpark_data)
        # Now, create the game payload using the ballpark_info
  #      game_payload = create_game_payload(game_info, home_team_info, away_team_info, ballpark_info, weather_info)
        

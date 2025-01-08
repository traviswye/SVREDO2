import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import time

# Suppress only the insecure request warning for localhost
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Base URLs for API endpoints
team_temp_tracking_api = "https://localhost:44346/api/TeamTemperatureTracking"  # To update the team temperature

# Team name normalization mapping to match abbreviations in the database
team_name_to_abbreviation = {
    "Arizona Diamondbacks": "ARI",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago White Sox": "CWS",
    "Chicago Cubs": "CHC",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Yankees": "NYY",
    "New York Mets": "NYM",
    "Oakland Athletics": "OAK",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD",
    "Seattle Mariners": "SEA",
    "San Francisco Giants": "SF",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH"
}

# Function to get game URLs for a specific date
def get_game_urls(year, month, day):
    url = f"https://www.baseball-reference.com/boxes/index.fcgi?year={year}&month={month}&day={day}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error fetching URL: Code: {response.status_code}: {url}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    game_links = []

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if '/boxes/' in href and href.endswith('.shtml'):
            game_links.append(f"https://www.baseball-reference.com{href}")
    
    return game_links

# Function to extract game information from a given game URL
def extract_game_info(game_url):
    response = requests.get(game_url)

    if response.status_code != 200:
        print(f"Error fetching game data from URL: {game_url}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract relevant game info
    content_div = soup.find('div', id='content')
    header = content_div.find('h1').get_text(strip=True)
    
    parts = header.split(' Box Score: ')
    teams_part = parts[0]
    away_team_name, home_team_name = teams_part.split(' vs ')
    
    # Extract and convert the game date
    raw_date = parts[1]
    game_date = datetime.strptime(raw_date, "%B %d, %Y").strftime("%Y-%m-%d")
    
    scorebox = soup.find('div', class_='scorebox')
    home_team_score = int(scorebox.find_all('div', class_='score')[1].get_text(strip=True))
    away_team_score = int(scorebox.find_all('div', class_='score')[0].get_text(strip=True))
    result = 'HomeWin' if home_team_score > away_team_score else 'AwayWin'

    # Build game info
    game_info = {
        'Date': game_date,
        'HomeTeamScore': home_team_score,
        'AwayTeamScore': away_team_score,
        'Result': result,
        'HomeTeamName': home_team_name,
        'AwayTeamName': away_team_name,
    }
    
    return game_info

# Function to process game and update TeamTemperatureTracking
def process_game(game_info):
    time.sleep(3)
    # Extract necessary information from game_info
    game_date = game_info['Date']
    home_team_name = game_info['HomeTeamName']
    away_team_name = game_info['AwayTeamName']
    home_team_score = game_info['HomeTeamScore']
    away_team_score = game_info['AwayTeamScore']
    result = game_info['Result']

    # Normalize team names to abbreviations
    home_team_abbreviation = team_name_to_abbreviation.get(home_team_name)
    away_team_abbreviation = team_name_to_abbreviation.get(away_team_name)

    if not home_team_abbreviation or not away_team_abbreviation:
        print(f"Error: Unable to find abbreviation for one of the teams: {home_team_name}, {away_team_name}")
        return

    # Get team temperature tracking for the home and away teams
    for team_abbreviation, score, opponent_score, is_winner in [
        (home_team_abbreviation, home_team_score, away_team_score, result == "HomeWin"),
        (away_team_abbreviation, away_team_score, home_team_score, result == "AwayWin")
    ]:
        # Fetch the most recent entry for the team using an updated endpoint
        response = requests.get(f"{team_temp_tracking_api}/latest/{team_abbreviation}/2024", verify=False)

        if response.status_code == 200:
            latest_entry = response.json()
            # Debug: print the response to understand its structure
            print(f"Latest entry for {team_abbreviation}: {latest_entry}")

            # Initialize previous values from the latest entry if they exist
            previous_temp = latest_entry["currentTemp"]
            previous_streak = latest_entry["streak"]
            wins = latest_entry["wins"]
            loses = latest_entry["loses"]
            runs_scored = latest_entry["rs"]
            runs_allowed = latest_entry["ra"]
            game_number = latest_entry["gameNumber"] + 1  # Increment game number for each new game
        else:
            print(f"Error: Could not fetch the latest data for team {team_abbreviation}")
            # Initialize default values for a new team entry
            previous_temp = 72
            previous_streak = 0
            wins = 0
            loses = 0
            runs_scored = 0
            runs_allowed = 0
            game_number = 1  # Start from 1 if no prior entry exists

        # Update metrics based on game result
        current_temp = previous_temp * 0.8959334
        streak = 0

        if is_winner:
            current_temp += 15
            wins += 1
            if previous_streak >= 0:
                streak = previous_streak + 1
            else:
                streak = 1
        else:
            loses += 1
            if previous_streak <= 0:
                streak = previous_streak - 1
            else:
                streak = -1

        runs_scored += score
        runs_allowed += opponent_score

        win_percentage = wins / (wins + loses) if (wins + loses) > 0 else 0.0
        pythag_win_percentage = (runs_scored ** 2) / ((runs_scored ** 2) + (runs_allowed ** 2)) if (runs_scored + runs_allowed) > 0 else 0.0

        # Build new record for posting
        new_entry = {
            "Team": team_abbreviation,
            "Year": 2024,
            "GameNumber": game_number,  # Include GameNumber
            "CurrentTemp": int(current_temp),
            "Wins": wins,
            "Loses": loses,
            "WinPerc": win_percentage,
            "RS": runs_scored,
            "RA": runs_allowed,
            "PythagPerc": pythag_win_percentage,  # Include updated pythag calculation
            "Streak": streak,
            "LastResult": f"{score}-{opponent_score}",
            "PreviousTemp": previous_temp,
            "Date": game_date
        }

        # Post the updated entry for the team
        response = requests.post(team_temp_tracking_api, headers={'Content-Type': 'application/json'}, data=json.dumps(new_entry), verify=False)

        if response.status_code == 201:
            print(f"Successfully updated temperature tracking for team {team_abbreviation} on {game_date}, Game {game_number}.")
        else:
            print(f"Error posting data for team {team_abbreviation}: {response.status_code} - {response.text}")



# Function to fetch and process games for each day
def process_games(start_date, end_date):
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    while current_date <= end_date:
        year = current_date.strftime('%Y')
        month = current_date.strftime('%m')
        day = current_date.strftime('%d')

        # Fetch the game URLs for the specific date
        game_urls = get_game_urls(year, month, day)
        print(f"Found {len(game_urls)} game URLs for {year}-{month}-{day}.")

        if len(game_urls) == 0:
            current_date += timedelta(days=1)
            continue  # Skip to the next date if no games are found

        # Process each game in the game URLs
        for game_url in game_urls:
            print(f"Processing game URL: {game_url}")
            game_info = extract_game_info(game_url)
            
            if game_info:
                # Process the game and update team temperature tracking
                process_game(game_info)

            # Add a delay to avoid rate-limiting
            time.sleep(1)

        # Move to the next day
        current_date += timedelta(days=1)

if __name__ == "__main__":
    start_date = '2024-09-19'  # Example start date
    end_date = '2024-09-29'  # Example end date
    process_games(start_date, end_date)

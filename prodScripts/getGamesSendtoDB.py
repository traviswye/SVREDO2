import requests
from bs4 import BeautifulSoup
import re
import logging
import time
import urllib3
import certifi

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ensure the certifi package is up to date
certifi.where()

TEAM_NAME_MAP = {
    "D-backs": "Diamondbacks",
    "D'backs": "Diamondbacks",
    "CWS": "White Sox",
    "CHW": "White Sox",
    # Add more mappings as needed
}

TEAM_ABBREV_MAP = {
    "ARI": "Diamondbacks",
    "ATL": "Braves",
    "BAL": "Orioles",
    "BOS": "Red Sox",
    "CHC": "Cubs",
    "CWS": "White Sox",
    "CHW": "White Sox",
    "CIN": "Reds",
    "CLE": "Guardians",
    "COL": "Rockies",
    "DET": "Tigers",
    "HOU": "Astros",
    "KC": "Royals",
    "KCR": "Royals",
    "LAA": "Angels",
    "LAD": "Dodgers",
    "MIA": "Marlins",
    "MIL": "Brewers",
    "MIN": "Twins",
    "NYM": "Mets",
    "NYY": "Yankees",
    "OAK": "Athletics",
    "PHI": "Phillies",
    "PIT": "Pirates",
    "SDP": "Padres",
    "SD": "Padres",
    "SEA": "Mariners",
    "SFG": "Giants",
    "SF": "Giants",
    "STL": "Cardinals",
    "TBR": "Rays",
    "TB": "Rays",
    "TEX": "Rangers",
    "TOR": "Blue Jays",
    "WSH": "Nationals",
    "WSN": "Nationals"
}


def standardize_team_name(team_name):
    """Standardize team name based on the dictionary mapping."""
    return TEAM_NAME_MAP.get(team_name, team_name)

# Setup logging
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='w', 
                    format='%(name)s - %(levelname)s - %(message)s')

def download_html(url, path):
    """Download HTML content from a URL and save it to a specified path."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',  # Do Not Track Request Header
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    try:
        response = requests.get(url, headers=headers, verify=False)  # Disable SSL verification
        response.raise_for_status()
        with open(path, 'w', encoding='utf-8') as file:
            file.write(response.text)
        logging.info(f"Content downloaded from {url} to {path}")
    except requests.HTTPError as e:
        logging.error(f"HTTP error occurred when accessing {url}: {e}")
    except requests.RequestException as e:
        logging.error(f"Request exception for {url}: {e}")
    except Exception as e:
        logging.error(f"Error writing data to {path}: {e}")

def get_player_id(url):
    """Extract player ID from the full URL."""
    match = re.search(r'/players/\w/(\w+)\.shtml', url)
    return match.group(1) if match else None

def build_split_url(player_id, year="2024"):
    """Construct split URL for the player."""
    return f"https://www.baseball-reference.com/players/split.fcgi?id={player_id}&year={year}&t=p"

def extract_game_info(game_summary):
    team_rows = game_summary.find('table', class_='teams').find_all('tr')
    away_team = standardize_team_name(team_rows[0].find('a').text)
    home_team = standardize_team_name(team_rows[1].find('a').text)
    preview_link = 'https://www.baseball-reference.com' + team_rows[0].find('a', string='Preview')['href']

    time_cell = team_rows[1].find('td', class_='right', string=lambda text: text and ("PM" in text or "AM" in text))
    game_time = time_cell.text.strip() if time_cell else "Time not available"

    pitcher_tables = game_summary.find_all('table')
    
    away_pitcher_id = "Unannounced"
    home_pitcher_id = "Unannounced"

    # Find the team abbreviations (e.g., "SDP", "PIT")
    team_abbrs = [abbr.text.strip() for abbr in game_summary.find_all('strong')]

    if len(team_abbrs) == 2:
        # If two abbreviations are found, proceed with normal two-pitcher handling
        pitcher_rows = pitcher_tables[1].find_all('tr')
        away_pitcher_url = pitcher_rows[0].find('a')['href'] if pitcher_rows[0].find('a') else None
        home_pitcher_url = pitcher_rows[1].find('a')['href'] if pitcher_rows[1].find('a') else None
        away_pitcher_id = get_player_id(away_pitcher_url) if away_pitcher_url else "Unannounced"
        home_pitcher_id = get_player_id(home_pitcher_url) if home_pitcher_url else "Unannounced"
    elif len(team_abbrs) == 1:
        # If only one abbreviation is found, determine which team it belongs to
        team_abbr = team_abbrs[0]
        full_team_name = TEAM_ABBREV_MAP.get(team_abbr, None)
        
        if full_team_name == home_team:
            home_pitcher_url = pitcher_tables[1].find('a')['href'] if pitcher_tables[1].find('a') else None
            home_pitcher_id = get_player_id(home_pitcher_url) if home_pitcher_url else "Unannounced"
        elif full_team_name == away_team:
            away_pitcher_url = pitcher_tables[1].find('a')['href'] if pitcher_tables[1].find('a') else None
            away_pitcher_id = get_player_id(away_pitcher_url) if away_pitcher_url else "Unannounced"
    elif len(team_abbrs) == 0:
        # If no abbreviations are found, both pitchers should be set to "Unannounced"
        away_pitcher_id = "Unannounced"
        home_pitcher_id = "Unannounced"

    return {
        'game_time': game_time,
        'away_team': away_team,
        'home_team': home_team,
        'preview_link': preview_link,
        'away_pitcher_id': away_pitcher_id,
        'home_pitcher_id': home_pitcher_id,
    }


def send_post_request(game_info, date):
    url = "https://localhost:44346/api/GamePreviews"
    payload = {
        "Date": date,
        "Time": game_info['game_time'],
        "HomeTeam": game_info['home_team'],
        "AwayTeam": game_info['away_team'],
        "HomePitcher": game_info.get('home_pitcher_id'),
        "AwayPitcher": game_info.get('away_pitcher_id'),
        "PreviewLink": game_info['preview_link']
    }
    
    try:
        response = requests.post(url, json=payload, verify=False)  # Disable SSL verification for localhost
        if response.status_code == 200:
            logging.info(f"Successfully posted game preview: {game_info['home_team']} vs {game_info['away_team']}")
        else:
            logging.error(f"Failed to post game preview: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logging.error(f"Request exception occurred: {e}")

def scrape_parent_url(parent_url):
    try:
        response = requests.get(parent_url, verify=False)  # Disable SSL verification
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        game_summaries = soup.find_all('div', class_='game_summary')

        if game_summaries:
            first_preview_link = 'https://www.baseball-reference.com' + game_summaries[0].find('a', string='Preview')['href']
            date_match = re.search(r'(\d{4})(\d{2})(\d{2})', first_preview_link)
            date = date_match.group(1) + "-" + date_match.group(2) + "-" + date_match.group(3)

            for game_summary in game_summaries:
                game_info = extract_game_info(game_summary)
                send_post_request(game_info, date)
                time.sleep(2)  # Add a 2-second delay between requests
            logging.info(f"Successfully scraped and posted all game previews for {date}")
        else:
            logging.warning(f"No game summaries found at {parent_url}")
    except requests.HTTPError as e:
        logging.error(f"HTTP error occurred when accessing {parent_url}: {e}")
    except requests.RequestException as e:
        logging.error(f"Request exception for {parent_url}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during scraping from {parent_url}: {e}")

# URL to scrape
parent_url = "https://www.baseball-reference.com/previews/"

# Scrape the parent URL
scrape_parent_url(parent_url)

from datetime import datetime, timedelta
import requests
import cloudscraper
from bs4 import BeautifulSoup
import urllib3
import random
import time
import json

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import requests and disable its warnings too
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Sample user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
]

# Team abbreviation mapping
TEAM_ABBREV_MAP = {
    "Diamondbacks": "ARI",
    "Braves": "ATL",
    "Orioles": "BAL",
    "Red Sox": "BOS",
    "Cubs": "CHC",
    "White Sox": "CHW",
    "Reds": "CIN",
    "Guardians": "CLE",
    "Rockies": "COL",
    "Tigers": "DET",
    "Astros": "HOU",
    "Royals": "KCR",
    "Angels": "LAA",
    "Dodgers": "LAD",
    "Marlins": "MIA",
    "Brewers": "MIL",
    "Twins": "MIN",
    "Mets": "NYM",
    "Yankees": "NYY",
    "Athletics": "OAK",
    "Phillies": "PHI",
    "Pirates": "PIT",
    "Padres": "SDP",
    "Mariners": "SEA",
    "Giants": "SFG",
    "Cardinals": "STL",
    "Rays": "TBR",
    "Rangers": "TEX",
    "Blue Jays": "TOR",
    "Nationals": "WSN"
}

# Create a cloudscraper session
def create_scraper_session():
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': random.choice(USER_AGENTS)
    }
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    scraper.headers.update(headers)
    return scraper

# Mimic human browsing behavior
def simulate_human_browsing(scraper):
    print("Simulating human browsing pattern...")
    
    # First visit the homepage
    homepage_url = "https://www.baseball-reference.com"
    print(f"Visiting homepage: {homepage_url}")
    homepage_response = scraper.get(homepage_url)
    
    if homepage_response.status_code != 200:
        print(f"Failed to access homepage: {homepage_response.status_code}")
        return False
    
    # Parse the homepage to find random links to visit
    soup = BeautifulSoup(homepage_response.content, "html.parser")
    links = soup.find_all("a", href=True)
    
    # Filter out external links, focus on internal navigation
    internal_links = [link['href'] for link in links if link['href'].startswith('/') 
                     and not link['href'].startswith('//') 
                     and not 'javascript:' in link['href']]
    
    # Visit 2-3 random pages to establish browsing pattern
    for _ in range(random.randint(2, 3)):
        if not internal_links:
            break
            
        random_link = random.choice(internal_links)
        internal_links.remove(random_link)
        
        full_url = f"https://www.baseball-reference.com{random_link}"
        print(f"Visiting random page: {full_url}")
        
        try:
            random_page_response = scraper.get(full_url)
            print(f"Status code: {random_page_response.status_code}")
            
            # Add random delay between page visits (2-5 seconds)
            delay = random.uniform(2, 5)
            print(f"Waiting for {delay:.2f} seconds...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"Error visiting random page: {e}")
    
    print("Human browsing simulation completed")
    return True

def get_current_date_formatted():
    """Get the current date formatted as YY-MM-DD for the API call."""
    current_date = datetime.now()
    return current_date.strftime('%y-%m-%d')

def get_teams_playing_today():
    """Get the list of teams playing today based on game previews."""
    try:
        # Format date for the API call
        date_str = get_current_date_formatted()
        url = f"https://localhost:44346/api/GamePreviews/{date_str}"
        
        # Use regular requests for API calls with proper SSL settings
        session = requests.Session()
        session.verify = False
        
        response = session.get(url)
        
        if response.status_code != 200:
            print(f"Failed to fetch game previews: {response.status_code}")
            return []
        
        game_previews = response.json()
        print(f"Found {len(game_previews)} games scheduled for today.")
        
        # Extract all teams playing today (both home and away)
        teams_playing = []
        for game in game_previews:
            home_team = game.get('homeTeam')
            away_team = game.get('awayTeam')
            
            # Convert team names to abbreviations
            if home_team in TEAM_ABBREV_MAP:
                teams_playing.append(TEAM_ABBREV_MAP[home_team])
            if away_team in TEAM_ABBREV_MAP:
                teams_playing.append(TEAM_ABBREV_MAP[away_team])
        
        # Remove duplicates
        teams_playing = list(set(teams_playing))
        print(f"Teams playing today: {teams_playing}")
        return teams_playing
    
    except Exception as e:
        print(f"Error fetching teams playing today: {e}")
        return []

def get_last_processed_game_number(team):
    """Get the last processed game number for a team to avoid duplicates."""
    try:
        url = f"https://localhost:44346/api/BullpenUsage/lastGameNumber/{team}/2025"
        
        # Use regular requests for API calls with proper SSL settings
        session = requests.Session()
        session.verify = False
        
        response = session.get(url)
        
        if response.status_code == 200:
            last_game = int(response.text)
            print(f"Last processed game for {team}: {last_game}")
            return last_game
        else:
            print(f"No previously processed games found for {team}. Starting from game 1.")
            return 0
    
    except Exception as e:
        print(f"Error fetching last processed game number: {e}")
        return 0

def parse_date(date_str, year):
    """Converts date like 'Sep 29' into 'YYYY-MM-DD' format."""
    date_str = date_str.replace("\xa0", " ")
    return datetime.strptime(f"{date_str} {year}", "%b %d %Y").strftime("%Y-%m-%d")

def get_park_factor(team):
    """Gets the park factor for the team."""
    url = f"https://localhost:44346/api/ParkFactors/getParkFactor?teamAbbreviation={team}"
    
    # Use regular requests for API calls with proper SSL settings
    session = requests.Session()
    session.verify = False
    
    response = session.get(url)
    if response.status_code == 200:
        return response.json()["parkFactorRating"]  # Extract park factor rating
    else:
        print(f"Failed to fetch park factor for team {team}. Status: {response.status_code}")
        return 0

def get_bbrefid(first_initial, last_name, team):
    """Gets the bbrefid for a pitcher."""
    url = f"https://localhost:44346/api/MLBPlayer/searchAbr?firstInitial={first_initial}&lastName={last_name}&team={team}"
    
    # Use regular requests for API calls with proper SSL settings
    session = requests.Session()
    session.verify = False
    
    response = session.get(url)
    if response.status_code == 200:
        data = response.json()
        if "bbrefId" in data:
            return data["bbrefId"]  # Extract only the bbrefId
    print(f"Failed to fetch bbrefid for {first_initial} {last_name} on team {team}. Status: {response.status_code}")
    return None

def extract_pitcher_data(pitcher_str, is_sp):
    """Extracts individual pitcher data from string."""
    try:
        name, stats = pitcher_str.split(" ")
        first_initial, last_name = name.split(".")
        stats = stats.strip("()")
        parts = stats.split("-")

        # Extract days of rest and SP score
        days_of_rest = int(parts[0]) if parts[0].isdigit() else 0
        sp_score = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0

        # Parse result suffixes
        results = {"W": 0, "H": 0, "L": 0, "Sv": 0, "Bsv": 0}
        for part in parts[1:]:
            for key in results.keys():
                if key in part:
                    results[key] = 1

        return {
            "firstInitial": first_initial,
            "lastName": last_name,
            "daysOfRest": days_of_rest,
            "SPscore": sp_score if is_sp else 0,
            **results
        }
    except Exception as e:
        print(f"Error extracting pitcher data: {e}")
        return None

def process_row(row, year, team):
    """Processes a single row of the table into a dictionary of game data."""
    try:
        # Locate the team game number
        team_game_number_cell = row.find('td', {'data-stat': 'team_game_num'})
        team_game_number = team_game_number_cell.get_text(strip=True) if team_game_number_cell else None

        # Other row data extraction
        date_pitched_cell = row.find('td', {'data-stat': 'date_game'})
        date_pitched_url = date_pitched_cell.find('a')['href'] if date_pitched_cell and date_pitched_cell.find('a') else None
        date_pitched = parse_date(date_pitched_cell.get_text(strip=True), year) if date_pitched_cell else None

        opponent = row.find('td', {'data-stat': 'opp_ID'}).get_text(strip=True) if row.find('td', {'data-stat': 'opp_ID'}) else None
        result = row.find('td', {'data-stat': 'game_result'}).get_text(strip=True) if row.find('td', {'data-stat': 'game_result'}) else None
        innings_pitched = row.find('td', {'data-stat': 'IP'}).get_text(strip=True) if row.find('td', {'data-stat': 'IP'}) else None
        extra_innings = 1 if innings_pitched and float(innings_pitched) > 9.0 else 0
        home_or_away = row.find('td', {'data-stat': 'homeORaway'}).get_text(strip=True) if row.find('td', {'data-stat': 'homeORaway'}) else None
        ballpark = opponent if home_or_away == "@" else "Home"
        pitchers_number = row.find('td', {'data-stat': 'pitchers_number'}).get_text(strip=True) if row.find('td', {'data-stat': 'pitchers_number'}) else None
        umpire = row.find('td', {'data-stat': 'umpire_hp'}).get_text(strip=True) if row.find('td', {'data-stat': 'umpire_hp'}) else None
        pitchers_used = row.find('td', {'data-stat': 'pitchers_number_desc'}).get_text(strip=True) if row.find('td', {'data-stat': 'pitchers_number_desc'}) else None

        # Prepare dictionary
        game_data = {
            "teamGameNumber": int(team_game_number) if team_game_number else None,
            "datePitched": date_pitched,
            "opponent": opponent,
            "result": result,
            "extraInnings": extra_innings,
            "homeOrAway": ballpark,
            "pitchersNumber": int(pitchers_number) if pitchers_number else None,
            "umpire": umpire,
            "boxScoreUrl": f"https://www.baseball-reference.com{date_pitched_url}" if date_pitched_url else None,
            "pitchersUsed": [p.strip() for p in pitchers_used.split(",")] if pitchers_used else [],
            "team": team
        }

        return game_data
    except Exception as e:
        print(f"Error processing row: {e}")
        return None

def process_game_data(game_data, missing_pitchers):
    """Processes the game data for each pitcher and posts it."""
    print("Processing game data for:", game_data)

    # Get park factor
    park_factor = get_park_factor(game_data["team"] if game_data["homeOrAway"] == "Home" else game_data["opponent"])
    game_data["parkFactor"] = park_factor

    # Extract SP score from the first pitcher
    sp_score = None
    if game_data["pitchersUsed"]:
        first_pitcher_data = extract_pitcher_data(game_data["pitchersUsed"][0], is_sp=True)
        if first_pitcher_data:
            sp_score = first_pitcher_data["SPscore"]

    # Process each pitcher
    for order, pitcher in enumerate(game_data["pitchersUsed"], start=1):
        is_sp = (order == 1)  # First pitcher is the SP
        pitcher_data = extract_pitcher_data(pitcher, is_sp)
        if not pitcher_data:
            print(f"Skipping invalid pitcher data: {pitcher}")
            continue

        print("Extracted Pitcher Data:", pitcher_data)

        # Get bbrefid
        bbrefid = get_bbrefid(pitcher_data["firstInitial"], pitcher_data["lastName"], game_data["team"])
        if not bbrefid:
            pitcher_name = f"{pitcher_data['firstInitial']}.{pitcher_data['lastName']}"
            if pitcher_name not in missing_pitchers:
                missing_pitchers.append(pitcher_name)
            print(f"Skipping pitcher {pitcher_name}, bbrefid not found.")
            continue

        # Build payload
        payload = {
            "bbrefid": bbrefid,
            "teamGameNumber": game_data["teamGameNumber"],
            "name": f"{pitcher_data['firstInitial']}.{pitcher_data['lastName']}",
            "team": game_data["team"],
            "year": 2025,  # Updated from 2024 to 2025
            "datePitched": game_data["datePitched"],
            "daysOfRest": pitcher_data["daysOfRest"],
            "pitcherOrder": order,
            "sPscore": pitcher_data["SPscore"],
            "win": pitcher_data["W"],
            "loss": pitcher_data["L"],
            "hold": pitcher_data["H"],
            "sv": pitcher_data["Sv"],
            "bsv": pitcher_data["Bsv"],
            "umpire": game_data["umpire"],
            "opponent": game_data["opponent"],
            "ballparkFactor": game_data["parkFactor"],
            "result": game_data["result"],
            "extraInnings": game_data["extraInnings"],
            "boxScoreUrl": game_data["boxScoreUrl"],
        }

        print("Payload being sent:", payload)
        post_bullpen_usage(payload)
        
        # Add a small delay between API calls
        time.sleep(random.uniform(0.5, 1.5))

def find_latest_game(rows, team, last_processed_game):
    """Find the latest game that hasn't been processed yet."""
    game_data_list = []
    
    # Get valid rows with team game numbers
    for row in rows:
        # Skip header rows and rows without data
        if not row.find('td'):
            continue
            
        # Get the team game number
        team_game_number_cell = row.find('td', {'data-stat': 'team_game_num'})
        if not team_game_number_cell:
            continue
            
        team_game_number_text = team_game_number_cell.get_text(strip=True)
        if not team_game_number_text.isdigit():
            continue
            
        team_game_number = int(team_game_number_text)
        
        # Only add games that haven't been processed yet
        if team_game_number > last_processed_game:
            game_data_list.append((team_game_number, row))
    
    # Sort by game number in descending order
    game_data_list.sort(key=lambda x: x[0], reverse=True)
    
    # Return the latest unprocessed game (would be at the start of the list)
    if game_data_list:
        print(f"Found latest unprocessed game: {game_data_list[0][0]}")
        return game_data_list[0][1]
    else:
        print(f"No new games found for {team} beyond game {last_processed_game}")
        return None

def process_latest_game(table, year, team, last_processed_game):
    """Process only the latest game that hasn't been processed yet."""
    rows = table.find_all('tr')
    print(f"Found {len(rows)} rows in the table.")
    
    # Find the row for the latest unprocessed game
    latest_game_row = find_latest_game(rows, team, last_processed_game)
    
    if latest_game_row:
        missing_pitchers = []
        game_data = process_row(latest_game_row, year, team)
        
        if game_data:
            print(f"Processing game {game_data['teamGameNumber']} for {team}...")
            process_game_data(game_data, missing_pitchers)
            
            # Report any missing pitchers
            if missing_pitchers:
                print(f"Pitchers with missing bbrefid for {team}: {missing_pitchers}")
        
        return True  # Return True if we processed a game
    
    return False  # Return False if no new game was processed

def post_bullpen_usage(payload):
    """Posts the payload to the BullpenUsage API."""
    url = "https://localhost:44346/api/BullpenUsage"
    
    # Use regular requests for API calls with proper SSL settings
    session = requests.Session()
    session.verify = False
    
    print("Payload being sent:", payload)  # Debugging payload
    response = session.post(url, json=payload)
    if response.status_code == 201:
        print(f"✓ Successfully posted data for {payload['bbrefid']}")
    else:
        print(f"✗ Failed to post data for {payload['bbrefid']}. Status: {response.status_code}")

def process_team(scraper, team, year=2025):
    """Process a single team for bullpen usage data."""
    print(f"\n==== Processing team {team} for year {year} ====")
    
    # Get the last processed game number to avoid duplicates
    last_processed_game = get_last_processed_game_number(team)
    
    # Fetch the table from Baseball-Reference
    url = f"https://www.baseball-reference.com/teams/tgl.cgi?team={team}&t=p&year={year}"
    print(f"Requesting data from: {url}")
    
    try:
        response = scraper.get(url)
        
        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code}")
            return False
            
        # Add small delay to mimic human reading time
        time.sleep(random.uniform(2, 4))
        
        # Check if we might be getting a captcha or empty response
        if len(response.content) < 5000:  # Suspiciously small response
            print(f"Warning: Very small response received ({len(response.content)} bytes). Possible captcha or block.")
            return False
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table_div = soup.find('div', id='div_team_pitching_gamelogs')
        if not table_div:
            print("Table div not found. This could be a structural change on the website or a block.")
            return False
            
        table = table_div.find('table', id='team_pitching_gamelogs') if table_div else None

        if table:
            return process_latest_game(table, year, team, last_processed_game)
        else:
            print("Table not found.")
            return False
    
    except Exception as e:
        print(f"Error fetching data: {e}")
        return False

def main(year=2025):
    """Main function to process only teams playing today."""
    print(f"=== Starting bullpen usage scraper for {year} (teams playing today only) ===")
    
    # Create a cloudscraper session
    scraper = create_scraper_session()
    
    # Simulate human browsing
    if not simulate_human_browsing(scraper):
        print("Failed to establish proper browsing session. Exiting.")
        return
    
    # Add random delay before starting the actual scraping
    delay = random.uniform(5, 10)
    print(f"Waiting for {delay:.2f} seconds before starting data collection...")
    time.sleep(delay)
    
    # Get teams playing today
    teams_playing = get_teams_playing_today()
    
    if not teams_playing:
        print("No games scheduled today or failed to fetch game data. Exiting.")
        return
    
    # Process each team playing today
    teams_processed = 0
    for team in teams_playing:
        print(f"\nProcessing team {team} ({teams_playing.index(team) + 1}/{len(teams_playing)})")
        if process_team(scraper, team, year):
            teams_processed += 1
        
        # Add delay between teams
        if team != teams_playing[-1]:  # Skip delay after the last team
            delay = random.uniform(15, 25)
            print(f"Waiting {delay:.2f} seconds before processing next team...")
            time.sleep(delay)
    
    print(f"\n=== Bullpen usage scraper completed ===")
    print(f"Processed {teams_processed} teams out of {len(teams_playing)} scheduled to play today.")

if __name__ == "__main__":
    main()
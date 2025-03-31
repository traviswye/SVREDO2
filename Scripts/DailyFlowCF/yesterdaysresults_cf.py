import cloudscraper
import requests
from bs4 import BeautifulSoup, Comment
from datetime import datetime, timedelta
import sys
import re
import json
import random
import pytz
import time
import urllib3

# Suppress only the insecure request warning for localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import requests and disable its warnings too
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

date2 = '24-09-04'
date = '20'+date2
# Define APIs to be used
gameOdds_api = f"https://localhost:44346/api/GameOdds/date/{date}"
gamepreviews_api = f"https://localhost:44346/api/GamePreviews/{date2}"
ballpark_api = "https://localhost:44346/api/ParkFactors"

# Team name normalization mapping
team_name_map = {
    "Arizona Diamondbacks": "Diamondbacks",
    "Atlanta Braves": "Braves",
    "Baltimore Orioles": "Orioles",
    "Boston Red Sox": "Red Sox",
    "Chicago White Sox": "White Sox",
    "Chicago Cubs": "Cubs",
    "Cincinnati Reds": "Reds",
    "Cleveland Guardians": "Guardians",
    "Colorado Rockies": "Rockies",
    "Detroit Tigers": "Tigers",
    "Houston Astros": "Astros",
    "Kansas City Royals": "Royals",
    "Los Angeles Angels": "Angels",
    "Los Angeles Dodgers": "Dodgers",
    "Miami Marlins": "Marlins",
    "Milwaukee Brewers": "Brewers",
    "Minnesota Twins": "Twins",
    "New York Yankees": "Yankees",
    "New York Mets": "Mets",
    "Oakland Athletics": "Athletics",
    "Philadelphia Phillies": "Phillies",
    "Pittsburgh Pirates": "Pirates",
    "San Diego Padres": "Padres",
    "San Francisco Giants": "Giants",
    "Seattle Mariners": "Mariners",
    "St. Louis Cardinals": "Cardinals",
    "Tampa Bay Rays": "Rays",
    "Texas Rangers": "Rangers",
    "Toronto Blue Jays": "Blue Jays",
    "Washington Nationals": "Nationals"
}

# Sample user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
]

# Create a cloudscraper session
def create_scraper_session():
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
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

# Function to get yesterday's date in the required format
def get_yesterday_date():
    yesterday = datetime.now() - timedelta(1)
    return yesterday.strftime('%Y'), yesterday.strftime('%m'), yesterday.strftime('%d')

def convert_date_format(raw_date):
    # Convert the date from "August 28, 2024" to "08-28-2024"
    date_obj = datetime.strptime(raw_date, "%B %d, %Y")
    formatted_date = date_obj.strftime("%m-%d-%Y")
    return formatted_date

def get_box_scores_url():
    year, month, day = get_yesterday_date()
    return f"https://www.baseball-reference.com/boxes/index.fcgi?year={year}&month={month}&day={day}"

# Updated get_game_urls to use cloudscraper
def get_game_urls(scraper, year, month, day):
    url = f"https://www.baseball-reference.com/boxes/index.fcgi?year={year}&month={month}&day={day}"
    
    try:
        print(f"Requesting box scores for {year}-{month}-{day} from: {url}")
        response = scraper.get(url)
        
        if response.status_code != 200:
            print(f"Error fetching URL: Code: {response.status_code}: {url}")
            return []

        # Add small delay to mimic human reading time
        time.sleep(random.uniform(1, 3))
        
        soup = BeautifulSoup(response.content, 'html.parser')
        game_links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if '/boxes/' in href and href.endswith('.shtml'):
                game_links.append(f"https://www.baseball-reference.com{href}")
        
        print(f"Found {len(game_links)} game links")
        return game_links
    
    except Exception as e:
        print(f"Error in get_game_urls: {e}")
        return []

# Function to extract the first pitcher from the comment's table after the correct team section
def extract_first_pitcher_id_from_comment_section(comment_soup, team_name):
    # Find the specific table for the team's pitching
    team_table_id = f"{team_name.replace(' ', '').replace('.', '')}pitching"
    team_table = comment_soup.find('table', id=team_table_id)
    
    if team_table:
        #print(f"Team table found for {team_name}")
        # Look for the first 'a' tag inside the correct team table
        pitcher_link = team_table.find('a', href=True)

        if pitcher_link:
            # Extract the player ID from the 'href', e.g., '/players/l/lynnla01.shtml'
            player_id = pitcher_link['href'].split('/')[-1].replace('.shtml', '')
            #print(f"Extracted pitcher ID: {player_id} from team section {team_name}")
            return player_id
        else:
            print(f"No pitcher link found in the table for {team_name}")
    else:
        print(f"No team table found for {team_name} with id {team_table_id}")
    
    return None

def extract_pitcher_from_comment(all_div, team_name):
    # Normalize the team name for matching, using regex for optional periods and spaces
    normalized_team_name = team_name.replace(" ", "").replace(".", "").lower()  # Make lowercase for case-insensitive search
    team_pitching_table_id = f"all_{normalized_team_name}pitching"

    # Find all comments and parse them
    comments = all_div.find_all(string=lambda text: isinstance(text, Comment))
    
    #print(f"Found {len(comments)} comments for team: {team_name}")

    for comment in comments:
        # Parse the comment with BeautifulSoup
        comment_soup = BeautifulSoup(comment, 'html.parser')

        # Use regex to match the team name, allowing for optional periods and spaces
        for div in comment_soup.find_all('div', id=True):
            div_id = div['id'].lower()  # Make lowercase for case-insensitive matching
            
            # Use regex to match team name variations, accounting for possible periods or spaces in the actual ID
            if re.match(f"all_{re.escape(normalized_team_name)}pitching", div_id):
                #print(f"Found team pitching section for {team_name}: {div_id}")

                # Extract the first pitcher from the pitching section
                first_pitcher_id = extract_first_pitcher_id_from_comment_section(comment_soup, team_name)
                if first_pitcher_id:
                    #print(f"Found pitcher ID: {first_pitcher_id} for team {team_name}")
                    return first_pitcher_id

    #print(f"No matching pitchers found for team {team_name}")
    return "Unknown"

# Updated scrape_game_data to use cloudscraper
def scrape_game_data(scraper, game_url):
    try:
        print(f"Requesting game data from: {game_url}")
        response = scraper.get(game_url)

        if response.status_code != 200:
            print(f"Error fetching game data from URL: {game_url}")
            return None

        # Add small delay to mimic human reading time
        time.sleep(random.uniform(2, 4))
        
        # Check if we might be getting a captcha or empty response
        if len(response.content) < 5000:  # Suspiciously small response
            print(f"Warning: Very small response received ({len(response.content)} bytes). Possible captcha or block.")
            # You could add additional handling here
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the relevant game info that was already present
        game_info = extract_game_info(soup)

        # Find all divs with "all" in their ID
        all_divs = soup.find_all('div', id=re.compile(r'.*all.*'))

        # Ensure we have enough divs to extract the SPs
        if len(all_divs) >= 5:
            # AwaySP is now located in the 4th occurrence of the 'all' div
            away_sp_div = all_divs[4]
            away_sp = extract_pitcher_from_comment(away_sp_div, game_info['AwayTeamName'])
            
            # HomeSP is now located in the 5th occurrence of the 'all' div
            home_sp_div = all_divs[4]  # Or all_divs[5] depending on structure
            home_sp = extract_pitcher_from_comment(home_sp_div, game_info['HomeTeamName'])  # No 'is_home' argument
        else:
            away_sp = "Unknown"
            home_sp = "Unknown"

        # Add the SP information to the game info
        game_info['AwaySP'] = away_sp
        game_info['HomeSP'] = home_sp

        return game_info
        
    except Exception as e:
        print(f"Error in scrape_game_data: {e}")
        return None

# Extract game information
def extract_game_info(soup):
    try:
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
        
        # Extract the NRFI check (No Runs First Inning)
        linescore_wrap = soup.find('div', class_='linescore_wrap')
        tbody_rows = linescore_wrap.find_all('tr')
        
        away_team_tds = [td for td in tbody_rows[1].find_all('td', class_='center')[1:] if td.get_text(strip=True) != ""]
        home_team_tds = [td for td in tbody_rows[2].find_all('td', class_='center')[1:] if td.get_text(strip=True) != ""]
        
        away_team_first_inning = int(away_team_tds[0].get_text(strip=True))
        home_team_first_inning = int(home_team_tds[0].get_text(strip=True))
        nrfi = (away_team_first_inning == 0) and (home_team_first_inning == 0)

        f5_away_score = sum(int(away_team_tds[i].get_text(strip=True)) for i in range(0, 5))  # Innings 1-5
        f5_home_score = sum(int(home_team_tds[i].get_text(strip=True)) for i in range(0, 5))

        if f5_away_score > f5_home_score:
            f5_result = 'AwayWin'
        elif f5_away_score < f5_home_score:
            f5_result = 'HomeWin'
        else:
            f5_result = 'Push'

        # Extract winning and losing pitcher
        tfoot = linescore_wrap.find('tfoot')
        if tfoot:
            pitcher_cells = tfoot.find_all('td')
            pitcher_text = " ".join([cell.get_text(strip=True) for cell in pitcher_cells])
            
            wp_match = re.search(r'WP:\s*([A-Za-z\s]+)', pitcher_text)
            lp_match = re.search(r'LP:\s*([A-Za-z\s]+)', pitcher_text)

            winning_pitcher = wp_match.group(1).replace('\xa0', ' ').strip() if wp_match else 'Unknown'
            losing_pitcher = lp_match.group(1).replace('\xa0', ' ').strip() if lp_match else 'Unknown'
        else:
            winning_pitcher = "Unknown"
            losing_pitcher = "Unknown"

        # Build game info
        game_info = {
            'Date': game_date,
            'HomeTeamScore': home_team_score,
            'AwayTeamScore': away_team_score,
            'Result': result,
            'ExtraInnings': len(away_team_tds) > 9,
            'HomeTeamName': home_team_name,
            'AwayTeamName': away_team_name,
            'WinningPitcher': winning_pitcher,
            'LosingPitcher': losing_pitcher,
            'nrfi': nrfi,
            'f5AwayScore': f5_away_score,
            'f5HomeScore': f5_home_score,
            'f5Result': f5_result
        }
        
        return game_info
    except Exception as e:
        print(f"Error in extract_game_info: {e}")
        return None

def normalize_team_name(team_name):
    return team_name_map.get(team_name, team_name)

def get_game_preview_id_and_time(game_info, game_previews):
    for preview in game_previews:
        if (normalize_team_name(game_info['HomeTeamName']) == preview['homeTeam'] and
                normalize_team_name(game_info['AwayTeamName']) == preview['awayTeam']):
            return preview['id'], preview['time']
    return 0, None  # Default to 0 and None if no match is found

def get_odds_id(game_info, odds):
    home_team = normalize_team_name(game_info['HomeTeamName'])
    away_team = normalize_team_name(game_info['AwayTeamName'])
    for odd in odds:
        if home_team == odd['homeTeam'] and away_team == odd['awayTeam']:
            return odd['id']
    return 0  # Default to 0 if no match is found

def fetch_additional_data():
    try:
        # Create a new session specifically for API calls with proper SSL settings
        session = requests.Session()
        session.verify = False
        
        game_preview_response = session.get(gamepreviews_api)
        odds_response = session.get(gameOdds_api)
        ballpark_response = session.get(ballpark_api)

        if game_preview_response.status_code == 200 and odds_response.status_code == 200 and ballpark_response.status_code == 200:
            game_previews = game_preview_response.json()
            odds = odds_response.json()
            ballpark_data = ballpark_response.json()
            return game_previews, odds, ballpark_data
        else:
            print(f"Error fetching game preview: {game_preview_response.status_code}")
            print(f"Error fetching odds data: {odds_response.status_code}")
            print(f"Error fetching ballpark data: {ballpark_response.status_code}")
            return None, None, None
    except Exception as e:
        print(f"Error in fetch_additional_data: {e}")
        return None, None, None

def build_game_object(game_info, gamePreviewID, oddsID, start_time):
    game_object = {
        "id": 0,
        "date": datetime.now().isoformat(),
        "time": start_time,  # Use the start_time from gamePreview
        "gamePreviewID": gamePreviewID,
        "oddsID": oddsID,
        "homeTeam": game_info['HomeTeamName'],
        "awayTeam": game_info['AwayTeamName'],
        "result": game_info['Result'],
        "homeTeamScore": game_info['HomeTeamScore'],
        "awayTeamScore": game_info['AwayTeamScore'],
        "winningPitcher": game_info.get("WinningPitcher", "Unknown"),
        "losingPitcher": game_info.get("LosingPitcher", "Unknown"),
        "nrfi": game_info['nrfi'],
        "f5AwayScore": game_info.get('f5AwayScore', 0),
        "f5HomeScore": game_info.get('f5HomeScore', 0),
        "f5Result": game_info.get('f5Result', "Unknown"),
        "dateModified": datetime.now().isoformat(),
        "AwaySP": game_info.get('AwaySP', "Unknown"),  # Use AwaySP from game_info
        "HomeSP": game_info.get('HomeSP', "Unknown")   # Use HomeSP from game_info
    }
    return game_object

# Function to fetch F5 odds data (using regular requests as it's not baseball-reference.com)
def get_f5_odds_data(date):
    url = f'https://www.sportsbookreview.com/betting-odds/mlb-baseball/money-line/1st-half/?date={date}'
    print(f"Requesting F5 odds data from: {url}")
    
    try:
        # Use regular requests with headers to appear more like a browser
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.sportsbookreview.com/betting-odds/mlb-baseball/',
            'Connection': 'keep-alive'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        script_tag = soup.find('script', id="__NEXT_DATA__")
        f5_odds_data = []

        if script_tag:
            json_data = json.loads(script_tag.string)
            games_data = json_data['props']['pageProps']['oddsTables'][0]['oddsTableModel']['gameRows']
            
            # Define the timezone objects
            utc_timezone = pytz.utc
            est_timezone = pytz.timezone("America/New_York")

            for game in games_data:
                game_view = game['gameView']
                home_team = game_view['homeTeam']['fullName']
                away_team = game_view['awayTeam']['fullName']
                start_time_utc = game_view['startDate']
                
                # Convert start time from UTC to EST
                game_datetime_utc = datetime.fromisoformat(start_time_utc.replace('Z', '+00:00')).replace(tzinfo=utc_timezone)
                game_datetime_est = game_datetime_utc.astimezone(est_timezone)
                game_date = game_datetime_est.strftime('%Y-%m-%d')
                game_time = game_datetime_est.strftime('%I:%M %p')

                # Extract BetMGM odds
                for odds_view in game['oddsViews']:
                    if odds_view and odds_view['sportsbook'] == 'betmgm':
                        home_odds = odds_view['currentLine']['homeOdds']
                        away_odds = odds_view['currentLine']['awayOdds']
                        f5_odds_object = {
                            "homeTeam": normalize_team_name(home_team),
                            "awayTeam": normalize_team_name(away_team),
                            "date": game_date,
                            "time": game_time,
                            "homeOdds": home_odds,
                            "awayOdds": away_odds
                        }
                        f5_odds_data.append(f5_odds_object)
                        break
        
        print(f"Found {len(f5_odds_data)} F5 odds entries")
        return f5_odds_data
    
    except Exception as e:
        print(f"Error in get_f5_odds_data: {e}")
        return []

def merge_game_data_and_odds(game_data, f5_odds_data):
    merged_data = []

    for game in game_data:
        for f5_odds in f5_odds_data:
            # Match by home and away teams
            if (normalize_team_name(game['homeTeam']) == f5_odds['homeTeam'] and
                normalize_team_name(game['awayTeam']) == f5_odds['awayTeam']):
                
                # Add F5 odds to the game object
                game['F5homeOdds'] = f5_odds['homeOdds']
                game['F5awayOdds'] = f5_odds['awayOdds']

                # Update the date and time from the F5 odds data
                game['date'] = f5_odds['date']  # Update the date
                game['time'] = f5_odds['time']  # Update the time

                # Append the updated game object to the merged data
                merged_data.append(game)
                break  # Stop further looping through f5_odds for this game

    return merged_data

def post_game_result(game_result):
    try:
        url = "https://localhost:44346/api/gameResults"
        
        # Create a new session specifically for API calls with proper SSL settings
        session = requests.Session()
        session.verify = False
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Post the game result data
        response = session.post(url, headers=headers, data=json.dumps(game_result))
        
        if response.status_code == 201:
            print(f"✓ Game result posted successfully: {game_result['homeTeam']} vs {game_result['awayTeam']}")
        else:
            print(f"✗ Failed to post game result: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Error in post_game_result: {e}")

# Updated main with improved logging and tracking
def save_progress(date, processed_urls):
    """Save progress to a file in case the script crashes"""
    try:
        with open('scraper_progress.json', 'w') as f:
            json.dump({
                'last_date': date.strftime('%Y-%m-%d'),
                'processed_urls': processed_urls
            }, f)
        print(f"Progress saved: {date.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"Error saving progress: {e}")

def load_progress():
    """Load progress from file if it exists"""
    try:
        with open('scraper_progress.json', 'r') as f:
            data = json.load(f)
            return data.get('last_date'), data.get('processed_urls', [])
    except FileNotFoundError:
        return None, []
    except Exception as e:
        print(f"Error loading progress: {e}")
        return None, []

def main(start_date=None, end_date=None):
    if not start_date or not end_date:
        print("Please provide a start and end date in 'YYYY-MM-DD' format.")
        return

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        print("Error: Incorrect date format. Please use 'YYYY-MM-DD'.")
        return
        
    # Check for saved progress
    saved_date, processed_urls = load_progress()
    if saved_date:
        resume_date = datetime.strptime(saved_date, '%Y-%m-%d')
        if resume_date >= start_date and resume_date < end_date:
            print(f"Found saved progress from {saved_date}. Would you like to resume? (y/n)")
            response = input().lower().strip()
            if response == 'y':
                start_date = resume_date
                print(f"Resuming from {start_date.strftime('%Y-%m-%d')}")
            else:
                processed_urls = []
                print("Starting fresh from the beginning")

    # Create a cloudscraper session for Baseball Reference
    scraper = create_scraper_session()
    
    # Track session validity
    session_valid = True
    session_reset_count = 0
    max_session_resets = 3
    
    # Simulate human browsing to establish cookies and session
    if not simulate_human_browsing(scraper):
        print("Failed to establish proper browsing session. Exiting.")
        return
    
    # Add random delay before starting actual scraping
    delay = random.uniform(5, 10)
    print(f"Waiting for {delay:.2f} seconds before starting data collection...")
    time.sleep(delay)

    current_date = start_date

    while current_date <= end_date:
        year = current_date.strftime('%Y')
        month = current_date.strftime('%m')
        day = current_date.strftime('%d')

        print(f"\n==== Processing games for {year}-{month}-{day} ====")
        
        # Fetch the game URLs for the specific date using cloudscraper
        game_urls = get_game_urls(scraper, year, month, day)
        
        # Check if we might be getting blocked (no URLs found when we expect some)
        if len(game_urls) == 0:
            # Only attempt to reset session if it's a date we expect to have games
            # (you can improve this logic based on your knowledge of baseball seasons)
            is_baseball_season = (3 <= int(month) <= 10)  # Assuming March-October is baseball season
            
            if is_baseball_season and session_valid and session_reset_count < max_session_resets:
                print(f"No games found for {year}-{month}-{day} during baseball season. Possible scraping detection.")
                print("Resetting session and trying again...")
                
                # Reset session
                scraper = create_scraper_session()
                session_reset_count += 1
                
                # Wait longer before retry
                wait_time = random.uniform(30, 60)
                print(f"Waiting {wait_time:.2f} seconds before retry...")
                time.sleep(wait_time)
                
                # Re-establish browsing pattern
                if simulate_human_browsing(scraper):
                    # Try again with new session
                    game_urls = get_game_urls(scraper, year, month, day)
                else:
                    session_valid = False
                    print("Failed to re-establish session. Continuing to next date.")
            
            # If still no games or we're not in season, move to next date
            if len(game_urls) == 0:
                print(f"No games found for {year}-{month}-{day}, moving to next date.")
                current_date += timedelta(days=1)
                continue  # Skip to the next date if no games are found

        # Fetch additional data from your API
        game_previews, odds, ballpark_data = fetch_additional_data()
        
        # Fetch F5 odds data from sportsbookreview.com (using regular requests)
        f5_odds_data = get_f5_odds_data(f"{year}-{month}-{day}")

        # List to store all game objects
        all_game_objects = []
        day_processed_urls = []

        for game_url in game_urls:
            # Skip already processed URLs if resuming
            if game_url in processed_urls:
                print(f"Skipping already processed game: {game_url}")
                continue
                
            # Use cloudscraper to fetch game data
            game_info = scrape_game_data(scraper, game_url)
            
            if game_info and game_previews and odds:
                gamePreviewID, start_time = get_game_preview_id_and_time(game_info, game_previews)
                oddsID = get_odds_id(game_info, odds)
                game_object = build_game_object(game_info, gamePreviewID, oddsID, start_time)
                all_game_objects.append(game_object)
                print(f"Processed game: {game_info['AwayTeamName']} vs {game_info['HomeTeamName']}")
                day_processed_urls.append(game_url)
            else:
                print(f"Skipped game due to missing data: {game_url}")
            
            # Add a delay to avoid rate-limiting
            sleep_time = random.uniform(3, 6)
            print(f"Waiting for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            
            # Save progress after each game
            processed_urls.extend(day_processed_urls)
            save_progress(current_date, processed_urls)

        # Merge game data with F5 odds data
        merged_data = merge_game_data_and_odds(all_game_objects, f5_odds_data)
        print(f"Successfully merged data for {len(merged_data)} games")

        # Post the merged data to the API
        for eachgame in merged_data:
            post_game_result(eachgame)
            time.sleep(random.uniform(0.5, 1.5))  # Small delay between API calls

        print(f"Completed processing for {year}-{month}-{day}")
        
        # Update processed URLs list
        processed_urls.extend(day_processed_urls)
        
        # Save progress at the end of each day
        save_progress(current_date, processed_urls)
        
        # Add a longer delay between processing different dates
        if current_date < end_date:
            date_delay = random.uniform(8, 15)
            print(f"Waiting for {date_delay:.2f} seconds before processing next date...")
            time.sleep(date_delay)
        
        current_date += timedelta(days=1)

if __name__ == "__main__":
    # Check if command-line arguments are provided
    if len(sys.argv) > 2:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
    else:
        # Default values
        start_date = '2025-03-29'
        end_date = '2025-03-29'

    # Call the main function with either command-line arguments or defaults
    main(start_date=start_date, end_date=end_date)
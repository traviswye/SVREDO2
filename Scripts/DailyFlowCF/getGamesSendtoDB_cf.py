import cloudscraper
import requests
from bs4 import BeautifulSoup
import re
import logging
import time
import urllib3
import certifi
import random

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import requests and disable its warnings too
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

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
    "ATH": "Athletics",
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

# Sample user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
]

# Setup logging
logging.basicConfig(level=logging.INFO, filename='preview_scraper.log', filemode='w', 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
    logging.info("Simulating human browsing pattern...")
    print("Simulating human browsing pattern...")
    
    # First visit the homepage
    homepage_url = "https://www.baseball-reference.com"
    print(f"Visiting homepage: {homepage_url}")
    homepage_response = scraper.get(homepage_url)
    
    if homepage_response.status_code != 200:
        logging.error(f"Failed to access homepage: {homepage_response.status_code}")
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
            logging.error(f"Error visiting random page: {e}")
            print(f"Error visiting random page: {e}")
    
    logging.info("Human browsing simulation completed")
    print("Human browsing simulation completed")
    return True

def standardize_team_name(team_name):
    """Standardize team name based on the dictionary mapping."""
    return TEAM_NAME_MAP.get(team_name, team_name)

def download_html(scraper, url, path):
    """Download HTML content from a URL and save it to a specified path."""
    try:
        print(f"Requesting content from: {url}")
        response = scraper.get(url)
        
        if response.status_code != 200:
            logging.error(f"HTTP error {response.status_code} when accessing {url}")
            return False
            
        with open(path, 'w', encoding='utf-8') as file:
            file.write(response.text)
        logging.info(f"Content downloaded from {url} to {path}")
        return True
    except Exception as e:
        logging.error(f"Error downloading from {url}: {e}")
        return False

def get_player_id(url):
    """Extract player ID from the full URL."""
    match = re.search(r'/players/\w/(\w+)\.shtml', url)
    return match.group(1) if match else None

def build_split_url(player_id, year="2024"):
    """Construct split URL for the player."""
    return f"https://www.baseball-reference.com/players/split.fcgi?id={player_id}&year={year}&t=p"

def extract_game_info(game_summary):
    """Extract game information from a game summary div."""
    try:
        team_rows = game_summary.find('table', class_='teams').find_all('tr')
        away_team = standardize_team_name(team_rows[0].find('a').text)
        home_team = standardize_team_name(team_rows[1].find('a').text)
        
        # Check if Preview link exists
        preview_link_elem = team_rows[0].find('a', string='Preview')
        if not preview_link_elem:
            logging.warning(f"No preview link found for {away_team} vs {home_team}")
            return None
            
        preview_link = 'https://www.baseball-reference.com' + preview_link_elem['href']

        time_cell = team_rows[1].find('td', class_='right', string=lambda text: text and ("PM" in text or "AM" in text))
        game_time = time_cell.text.strip() if time_cell else "Time not available"

        pitcher_tables = game_summary.find_all('table')
        
        away_pitcher_id = "Unannounced"
        home_pitcher_id = "Unannounced"

        # Find the team abbreviations (e.g., "SDP", "PIT")
        team_abbrs = [abbr.text.strip() for abbr in game_summary.find_all('strong')]

        if len(team_abbrs) == 2:
            # If two abbreviations are found, proceed with normal two-pitcher handling
            if len(pitcher_tables) > 1:
                pitcher_rows = pitcher_tables[1].find_all('tr')
                if len(pitcher_rows) >= 2:
                    away_pitcher_link = pitcher_rows[0].find('a')
                    home_pitcher_link = pitcher_rows[1].find('a')
                    
                    away_pitcher_url = away_pitcher_link['href'] if away_pitcher_link else None
                    home_pitcher_url = home_pitcher_link['href'] if home_pitcher_link else None
                    
                    away_pitcher_id = get_player_id(away_pitcher_url) if away_pitcher_url else "Unannounced"
                    home_pitcher_id = get_player_id(home_pitcher_url) if home_pitcher_url else "Unannounced"
        elif len(team_abbrs) == 1:
            # If only one abbreviation is found, determine which team it belongs to
            team_abbr = team_abbrs[0]
            full_team_name = TEAM_ABBREV_MAP.get(team_abbr, None)
            
            if len(pitcher_tables) > 1 and pitcher_tables[1].find('a'):
                pitcher_url = pitcher_tables[1].find('a')['href']
                pitcher_id = get_player_id(pitcher_url) if pitcher_url else "Unannounced"
                
                if full_team_name == home_team:
                    home_pitcher_id = pitcher_id
                elif full_team_name == away_team:
                    away_pitcher_id = pitcher_id

        return {
            'game_time': game_time,
            'away_team': away_team,
            'home_team': home_team,
            'preview_link': preview_link,
            'away_pitcher_id': away_pitcher_id,
            'home_pitcher_id': home_pitcher_id,
        }
    except Exception as e:
        logging.error(f"Error extracting game info: {e}")
        return None

def send_post_request(game_info, date):
    """Send POST request to the API with game preview data."""
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
        # Create a new session specifically for API calls with proper SSL settings
        session = requests.Session()
        session.verify = False
        
        # Use the session to make the API call
        response = session.post(url, json=payload)
        
        if response.status_code == 200 or response.status_code == 201:
            logging.info(f"✓ Successfully posted game preview: {game_info['home_team']} vs {game_info['away_team']}")
            print(f"✓ Posted: {game_info['home_team']} vs {game_info['away_team']}")
            return True
        else:
            logging.error(f"✗ Failed to post game preview: {response.status_code} - {response.text}")
            print(f"✗ Failed to post: {game_info['home_team']} vs {game_info['away_team']}: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"✗ Error sending data to API: {e}")
        print(f"✗ Error sending data to API: {e}")
        return False

def scrape_previews_page(scraper, parent_url, max_retries=3):
    """Scrape the baseball previews page for upcoming games."""
    retries = 0
    while retries < max_retries:
        try:
            print(f"Requesting previews from: {parent_url}")
            response = scraper.get(parent_url)
            
            if response.status_code != 200:
                logging.error(f"HTTP error {response.status_code} when accessing {parent_url}")
                print(f"HTTP error {response.status_code} when accessing {parent_url}")
                retries += 1
                time.sleep(5)
                continue
                
            # Add delay to mimic human reading
            time.sleep(random.uniform(2, 4))
            
            # Check if we might be getting a captcha or empty response
            if len(response.content) < 5000:  # Suspiciously small response
                logging.warning(f"Warning: Very small response received ({len(response.content)} bytes). Possible captcha or block.")
                print(f"Warning: Very small response received. Possible captcha or block.")
                retries += 1
                if retries < max_retries:
                    # Wait longer before retrying
                    delay = random.uniform(20, 30)
                    print(f"Waiting {delay:.2f} seconds before retrying...")
                    time.sleep(delay)
                    
                    # Reset session and retry
                    scraper = create_scraper_session()
                    if not simulate_human_browsing(scraper):
                        logging.error("Failed to establish proper browsing session.")
                        print("Failed to establish proper browsing session.")
                        return False
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            game_summaries = soup.find_all('div', class_='game_summary')

            if not game_summaries:
                logging.warning(f"No game summaries found at {parent_url}")
                print(f"No game summaries found at {parent_url}")
                return False

            # Extract date from first preview link if available
            date = None
            for game_summary in game_summaries:
                preview_link_elem = game_summary.find('a', string='Preview')
                if preview_link_elem:
                    first_preview_link = 'https://www.baseball-reference.com' + preview_link_elem['href']
                    date_match = re.search(r'(\d{4})(\d{2})(\d{2})', first_preview_link)
                    if date_match:
                        date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                        break

            if not date:
                logging.warning("Could not determine date from preview links")
                print("Could not determine date from preview links")
                return False
                
            print(f"Found {len(game_summaries)} game summaries for {date}")
            
            # Process each game summary
            success_count = 0
            for i, game_summary in enumerate(game_summaries):
                print(f"Processing game {i+1}/{len(game_summaries)}...")
                game_info = extract_game_info(game_summary)
                
                if game_info:
                    if send_post_request(game_info, date):
                        success_count += 1
                
                # Add a delay between requests to appear more human-like
                if i < len(game_summaries) - 1:  # Don't delay after the last one
                    delay = random.uniform(1.5, 3.5)
                    time.sleep(delay)
                    
            logging.info(f"Successfully processed {success_count}/{len(game_summaries)} game previews for {date}")
            print(f"Successfully processed {success_count}/{len(game_summaries)} game previews for {date}")
            return True
                
        except Exception as e:
            logging.error(f"Error scraping previews page: {e}")
            print(f"Error scraping previews page: {e}")
            retries += 1
            
            if retries < max_retries:
                delay = random.uniform(10, 20)
                print(f"Retrying in {delay:.2f} seconds... (Attempt {retries+1}/{max_retries})")
                time.sleep(delay)
    
    logging.error(f"Failed to scrape previews page after {max_retries} attempts")
    print(f"Failed to scrape previews page after {max_retries} attempts")
    return False

def main():
    # URL to scrape
    parent_url = "https://www.baseball-reference.com/previews"
    
    logging.info("Starting preview scraper")
    print("Starting baseball preview scraper")
    
    # Create a cloudscraper session
    scraper = create_scraper_session()
    
    # Simulate human browsing to establish cookies and session
    if not simulate_human_browsing(scraper):
        logging.error("Failed to establish proper browsing session. Exiting.")
        print("Failed to establish proper browsing session. Exiting.")
        return
    
    # Add random delay before starting actual scraping
    delay = random.uniform(5, 10)
    print(f"Waiting for {delay:.2f} seconds before starting data collection...")
    time.sleep(delay)
    
    # Scrape the previews page
    scrape_previews_page(scraper, parent_url)
    
    logging.info("Preview scraper completed")
    print("Preview scraper completed")

if __name__ == "__main__":
    main()
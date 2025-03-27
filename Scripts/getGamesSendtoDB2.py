import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import logging
import time
import sys
import os
import urllib3
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging to output to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('baseball_scraper.log', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

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

# Special team codes used in Baseball-Reference preview URLs
TEAM_PREVIEW_CODES = {
    "Diamondbacks": "ARI",
    "Braves": "ATL",
    "Orioles": "BAL",
    "Red Sox": "BOS",
    "Cubs": "CHN",
    "White Sox": "CHA",
    "Reds": "CIN",
    "Guardians": "CLE",
    "Rockies": "COL",
    "Tigers": "DET",
    "Astros": "HOU",
    "Royals": "KCA",
    "Angels": "LAA",
    "Dodgers": "LAN",
    "Marlins": "MIA",
    "Brewers": "MIL",
    "Twins": "MIN",
    "Mets": "NYN",
    "Yankees": "NYA",
    "Athletics": "ATH",
    "Phillies": "PHI",
    "Pirates": "PIT",
    "Padres": "SDN",
    "Mariners": "SEA",
    "Giants": "SFN",
    "Cardinals": "SLN",
    "Rays": "TBA",
    "Rangers": "TEX",
    "Blue Jays": "TOR",
    "Nationals": "WAS"
}

def setup_driver(chromedriver_path, headless=True):
    """Set up and return a configured Chrome WebDriver"""
    logger.info("Setting up Chrome WebDriver...")
    
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
    
    # Skip SSL certificate verification (for corporate environments)
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    
    # Initialize the Chrome WebDriver with the configured options
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def standardize_team_name(team_name):
    """Standardize team name based on the dictionary mapping."""
    return TEAM_NAME_MAP.get(team_name, team_name)

def get_player_id(url):
    """Extract player ID from the full URL."""
    if not url:
        logger.warning("Attempted to extract player ID from None URL")
        return "Unannounced"
    
    match = re.search(r'/players/\w/(\w+)\.shtml', url)
    result = match.group(1) if match else None
    
    if not result:
        logger.warning(f"Could not extract player ID from URL: {url}")
        return "Unannounced"
    
    return result

def generate_preview_link(home_team, date_obj):
    """Generate a preview link in the format /previews/YYYY/TTT########0.shtml"""
    # Get the team code for the preview URL
    team_code = TEAM_PREVIEW_CODES.get(home_team, "")
    if not team_code:
        logger.warning(f"Could not find team code for {home_team}, using default")
        # Try to derive a code if we don't have a mapping
        team_code = home_team[:3].upper()
    
    # Format the date part (YYYYMMDD)
    date_str = date_obj.strftime("%Y%m%d")
    year = date_obj.strftime("%Y")
    
    # Build the preview link
    preview_link = f"https://www.baseball-reference.com/previews/{year}/{team_code}{date_str}0.shtml"
    logger.info(f"Generated preview link for {home_team}: {preview_link}")
    
    return preview_link

def extract_game_info(driver, game_summary, index=0, game_date=None):
    """Extract game information from a game summary element"""
    try:
        logger.info(f"Extracting game info from game summary #{index}")
        
        # Find the teams table
        teams_table = game_summary.find_element(By.CSS_SELECTOR, "table.teams")
        if not teams_table:
            logger.warning(f"Teams table not found in game summary #{index}")
            return None
            
        team_rows = teams_table.find_elements(By.TAG_NAME, "tr")
        if len(team_rows) < 2:
            logger.warning(f"Not enough team rows found in game summary #{index}")
            return None
        
        # Get team names
        try:
            away_team_link = team_rows[0].find_element(By.TAG_NAME, "a")
            home_team_link = team_rows[1].find_element(By.TAG_NAME, "a")
            
            away_team = standardize_team_name(away_team_link.text)
            home_team = standardize_team_name(home_team_link.text)
            
            logger.info(f"Teams: {away_team} @ {home_team}")
        except Exception as e:
            logger.error(f"Error extracting team names: {e}")
            return None
        
        # Look for the preview link in the HTML first
        preview_link = None
        try:
            link_elements = teams_table.find_elements(By.TAG_NAME, "a")
            for link in link_elements:
                if link.text == "Preview":
                    preview_link = link.get_attribute("href")
                    logger.info(f"Found preview link: {preview_link}")
                    break
        except Exception as e:
            logger.warning(f"Error looking for preview link: {e}")
        
        # Generate preview link if not found
        if not preview_link and game_date:
            preview_link = generate_preview_link(home_team, game_date)
        
        # Get game time
        try:
            time_cells = team_rows[1].find_elements(By.CSS_SELECTOR, "td.right")
            game_time = "Time not available"
            for cell in time_cells:
                cell_text = cell.text
                if "PM" in cell_text or "AM" in cell_text:
                    game_time = cell_text.strip()
                    break
            
            logger.info(f"Game time: {game_time}")
        except Exception as e:
            logger.error(f"Error extracting game time: {e}")
            game_time = "Time not available"
        
        # Get pitcher information
        away_pitcher_id = "Unannounced"
        home_pitcher_id = "Unannounced"
        
        try:
            # Find all tables in the game summary
            pitcher_tables = game_summary.find_elements(By.TAG_NAME, "table")
            logger.info(f"Found {len(pitcher_tables)} tables in game summary")
            
            # Find team abbreviations
            team_abbrs = []
            strong_elements = game_summary.find_elements(By.TAG_NAME, "strong")
            for elem in strong_elements:
                if elem.text.strip():
                    team_abbrs.append(elem.text.strip())
            
            logger.info(f"Team abbreviations found: {team_abbrs}")
            
            if len(team_abbrs) == 2 and len(pitcher_tables) > 1:
                # Two teams with pitchers
                pitcher_rows = pitcher_tables[1].find_elements(By.TAG_NAME, "tr")
                
                if len(pitcher_rows) > 0:
                    away_pitcher_links = pitcher_rows[0].find_elements(By.TAG_NAME, "a")
                    if away_pitcher_links:
                        away_pitcher_url = away_pitcher_links[0].get_attribute("href")
                        away_pitcher_id = get_player_id(away_pitcher_url)
                
                if len(pitcher_rows) > 1:
                    home_pitcher_links = pitcher_rows[1].find_elements(By.TAG_NAME, "a")
                    if home_pitcher_links:
                        home_pitcher_url = home_pitcher_links[0].get_attribute("href")
                        home_pitcher_id = get_player_id(home_pitcher_url)
            
            elif len(team_abbrs) == 1 and len(pitcher_tables) > 1:
                # One team with pitcher
                team_abbr = team_abbrs[0]
                full_team_name = TEAM_ABBREV_MAP.get(team_abbr, None)
                
                if full_team_name == home_team:
                    pitcher_links = pitcher_tables[1].find_elements(By.TAG_NAME, "a")
                    if pitcher_links:
                        home_pitcher_url = pitcher_links[0].get_attribute("href")
                        home_pitcher_id = get_player_id(home_pitcher_url)
                elif full_team_name == away_team:
                    pitcher_links = pitcher_tables[1].find_elements(By.TAG_NAME, "a")
                    if pitcher_links:
                        away_pitcher_url = pitcher_links[0].get_attribute("href")
                        away_pitcher_id = get_player_id(away_pitcher_url)
        except Exception as e:
            logger.error(f"Error extracting pitcher information: {e}")
        
        logger.info(f"Extracted pitchers - Away: {away_pitcher_id}, Home: {home_pitcher_id}")
        
        return {
            'game_time': game_time,
            'away_team': away_team,
            'home_team': home_team,
            'preview_link': preview_link,
            'away_pitcher_id': away_pitcher_id,
            'home_pitcher_id': home_pitcher_id,
        }
    
    except Exception as e:
        logger.error(f"Error extracting game info: {e}")
        return None

def get_date_from_title(title):
    """Extract date from page title"""
    try:
        date_pattern = r'MLB Probable Pitchers for (.*?)\s*\|'
        match = re.search(date_pattern, title)
        if match:
            date_str = match.group(1)
            logger.info(f"Found date in title: {date_str}")
            
            # Parse the date
            date_formats = [
                "%A, %B %d, %Y",  # Thursday, March 27, 2025
                "%B %d, %Y",      # March 27, 2025
                "%a, %b %d, %Y"   # Thu, Mar 27, 2025
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date
                except ValueError:
                    continue
            
            logger.warning(f"Could not parse date string: {date_str}")
    except Exception as e:
        logger.error(f"Error extracting date from title: {e}")
    
    # Return today's date if we couldn't extract from title
    return datetime.now()

def send_post_request(game_info, date_str):
    """Send game information to the API"""
    url = "https://localhost:44346/api/GamePreviews"
    payload = {
        "Date": date_str,
        "Time": game_info['game_time'],
        "HomeTeam": game_info['home_team'],
        "AwayTeam": game_info['away_team'],
        "HomePitcher": game_info.get('home_pitcher_id'),
        "AwayPitcher": game_info.get('away_pitcher_id'),
        "PreviewLink": game_info['preview_link']
    }
    
    logger.info(f"Sending POST request to {url} with payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, verify=False)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text[:100]}..." if len(response.text) > 100 else response.text)
        
        if response.status_code == 200:
            logger.info(f"Successfully posted game preview: {game_info['home_team']} vs {game_info['away_team']}")
            return True
        else:
            logger.error(f"Failed to post game preview: {response.status_code} - {response.text}")
            return False
    except requests.RequestException as e:
        logger.error(f"Request exception occurred: {e}")
        return False

def scrape_previews_with_selenium(chromedriver_path):
    """Scrape Baseball Reference previews page using Selenium"""
    logger.info("Starting to scrape baseball-reference.com/previews/ using Selenium")
    
    driver = setup_driver(chromedriver_path, headless=True)
    url = "https://www.baseball-reference.com/previews/"
    
    try:
        # Navigate to the previews page
        logger.info(f"Accessing URL: {url}")
        driver.get(url)
        
        # Wait for Cloudflare challenge to complete
        logger.info("Waiting for page to load (allowing time for Cloudflare challenge)...")
        time.sleep(10)  # Wait for Cloudflare to process
        
        # Check if we're still on the Cloudflare page
        if "Just a moment" in driver.title:
            logger.warning("Still on Cloudflare challenge page after waiting. Extending wait time...")
            time.sleep(10)  # Wait longer
            
            # Check again
            if "Just a moment" in driver.title:
                logger.error("Failed to bypass Cloudflare challenge after extended wait")
                return
        
        logger.info(f"Page title: {driver.title}")
        logger.info("Successfully loaded page. Looking for game summaries...")
        
        # Find game summaries
        game_summaries = driver.find_elements(By.CSS_SELECTOR, "div.game_summary")
        logger.info(f"Found {len(game_summaries)} game summaries")
        
        if not game_summaries:
            logger.warning("No game summaries found. Page might not have any games scheduled.")
            # Save the HTML for debugging
            with open('no_games_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info("Saved page HTML to no_games_page.html for debugging")
            return
        
        # Get the date from the page title
        date_obj = get_date_from_title(driver.title)
        date_str = date_obj.strftime("%Y-%m-%d")
        logger.info(f"Using date: {date_str}")
        
        # Process each game summary
        successful_posts = 0
        for i, game_summary in enumerate(game_summaries):
            logger.info(f"Processing game summary #{i+1}")
            game_info = extract_game_info(driver, game_summary, i+1, date_obj)
            
            if game_info:
                if send_post_request(game_info, date_str):
                    successful_posts += 1
                logger.info(f"Waiting 2 seconds before processing next game...")
                time.sleep(2)  # Add a 2-second delay between requests
            else:
                logger.warning(f"Skipping game summary #{i+1} due to extraction failure")
        
        logger.info(f"Successfully scraped and posted {successful_posts} out of {len(game_summaries)} game previews for {date_str}")
    
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
    finally:
        logger.info("Closing WebDriver...")
        driver.quit()

if __name__ == "__main__":
    # Set path to ChromeDriver
    default_chromedriver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
    
    # Allow specifying chromedriver path as command-line argument
    chromedriver_path = sys.argv[1] if len(sys.argv) > 1 else default_chromedriver_path
    
    if not os.path.exists(chromedriver_path):
        logger.error(f"ChromeDriver not found at {chromedriver_path}")
        logger.error("Please download ChromeDriver from https://googlechromelabs.github.io/chrome-for-testing/")
        logger.error("and place it in the same directory as this script or specify the path as an argument.")
        sys.exit(1)
    
    logger.info(f"Using ChromeDriver at {chromedriver_path}")
    
    # Scrape the previews page
    scrape_previews_with_selenium(chromedriver_path)